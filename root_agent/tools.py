def save_application(aadhaar_number: str, applicant_name: str, phone_number: str, scheme_name: str) -> str:
    """
    Saves the application record to the database

    Args:
        aadhaar_number: The applicant's Aadhaar number (must be at least 4 digits).
        applicant_name: The applicant's full name.
        phone_number: The applicant's phone number.
        scheme_name: The name of the scheme they are applying for.

    Returns:
        A JSON string containing the message and the newly generated application ID.
    """
    import sqlite3
    from datetime import datetime
    import os
    import json

    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S") 

    if aadhaar_number and len(aadhaar_number) >= 4:
        aadhaar_last_four = aadhaar_number[-4:]
    else:
        aadhaar_last_four = "0000"

    app_id = f"KN-{date_str}-{time_str}-{aadhaar_last_four}"

    timestamp = now
    status = "Submitted"

    from dotenv import load_dotenv
    load_dotenv()

    DB_FILE = os.getenv("APPLICATION_DB_PATH")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute(
        """INSERT INTO applications
           (application_id, aadhaar_number, applicant_name, phone_number, scheme_name, status, timestamp) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (app_id, aadhaar_number, applicant_name, phone_number, scheme_name, status, timestamp)
    )
    conn.commit()
    conn.close()
    
    return json.dumps({
        "message": "Application record created successfully.",
        "application_id": app_id
    })

async def check_application_status(application_uuid: str) -> dict:
    """
    Fetch the status of a scheme application by its UUID.

    Args:
        application_uuid (str): Unique application ID

    Returns:
        dict: { "application_uuid": str, "status": str } if found,
              { "error": "Application not found" } otherwise
    """
    import sqlite3, os

    from dotenv import load_dotenv
    load_dotenv()

    DB_PATH = os.getenv("APPLICATION_DB_PATH")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT application_uuid, scheme_name, status
        FROM applications
        WHERE application_uuid = ?
        """, (application_uuid,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"application_uuid": row[0], "scheme_name": row[1], "status": row[2]}
    else:
        return {"error": "Application not found"}
    
async def calculate_age(dob_str):
    from datetime import datetime, date
    born = datetime.strptime(dob_str, "%Y-%m-%d").date()
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

async def fetch_user_profile(aadhaar_number: str) -> str:
    """
    Simulates fetching user data from DigiLocker using their Aadhaar number.
    It retrieves the user's profile from a local database.

    Args:
        aadhaar_number: The 12-digit Aadhaar number of the user.

    Returns:
        A JSON string containing the user's profile if found, otherwise an error message.
    """
    import sqlite3
    import json, os

    from dotenv import load_dotenv
    load_dotenv()

    DB_PATH = os.getenv("USERS_DB_PATH")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_details WHERE aadhaar_number = ?", (aadhaar_number,))
    user = cursor.fetchone()
    conn.close()
    if user:
        user_dict = dict(user)
        user_dict['age'] = await calculate_age(user_dict['dob'])
        return json.dumps(user_dict)
    else:
        return json.dumps({"error": "No user profile found for the provided Aadhaar number."})
    

async def find_eligible_schemes(user_profile_json: str = "{}", scheme_name: str = "") -> str:
    """
    Finds government schemes from the database. It can perform three types of searches:
    1. Personalized Search: Finds schemes a user is eligible for based on their profile.
    2. Specific Search: Fetches details for a specific scheme by name.
    3. General Search: Lists all available schemes.

    This version now returns the 'required_information' and 'supporting_documents' for each scheme,
    which is essential for the agent's application flow.

    Args:
        user_profile_json: A JSON string containing a user's profile (age, gender, income, community, district).
        scheme_name: The partial or full name of a specific scheme to search for.

    Returns:
        A JSON string containing a list of matching schemes, including lists for required information and documents.
    """
    import sqlite3
    import json
    import os
    from dotenv import load_dotenv

    load_dotenv()
    DB_PATH = os.getenv("SCHEMES_DB_PATH")

    if not os.path.exists(DB_PATH):
        return json.dumps({"error": f"Database file not found at path: {DB_PATH}"})

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    base_query = """
        SELECT
            s.id, s.name, d.name as department_name, s.definition,
            s.eligibility_summary, s.application_fee,
            s.required_information, s.supporting_documents
        FROM schemes s
        JOIN departments d ON s.department_id = d.id
        JOIN scheme_geographies sg ON s.id = sg.scheme_id
    """
    params = []
    conditions = []

    if scheme_name:
        conditions.append("s.name LIKE ?")
        params.append(f"%{scheme_name}%")
    else:
        try:
            profile = json.loads(user_profile_json)
            if profile:
                if 'age' in profile:
                    conditions.append("(s.min_age <= ? AND s.max_age >= ?)")
                    params.extend([profile['age']])
                if 'gender' in profile:
                    conditions.append("s.gender_eligibility IN (?, 'Any')")
                    params.append(profile['gender'])
                if 'annual_income' in profile:
                    conditions.append("s.max_annual_income >= ?")
                    params.append(profile['annual_income'])
                if 'district' in profile:
                    conditions.append("(sg.district = ? OR sg.district = 'All Districts')")
                    params.append(profile['district'])
                if 'community' in profile:
                    conditions.append("EXISTS (SELECT 1 FROM json_each(s.community_eligibility) WHERE value = ? OR value = 'General')")
                    params.append(profile['community'])
        except (json.JSONDecodeError, KeyError):
            pass

    if conditions:
        query = f"{base_query} WHERE {' AND '.join(conditions)} GROUP BY s.id"
    else:
        query = f"{base_query} GROUP BY s.id"

    cursor.execute(query, params)
    schemes_raw = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # PROCESS JSON FIELDS: Convert the JSON strings from the DB into actual lists for the agent to use.
    for scheme in schemes_raw:
        scheme['required_information'] = json.loads(scheme.get('required_information') or '[]')
        scheme['supporting_documents'] = json.loads(scheme.get('supporting_documents') or '[]')

    if not schemes_raw:
        return json.dumps({"message": "No schemes found matching your criteria."})
    
    return json.dumps(schemes_raw)

async def get_all_schemes_with_criteria(scheme_name: str = "") -> str:
    """
    Fetches a list of government schemes along with all their eligibility criteria.

    Args:
        scheme_name: If provided, fetches only the specific scheme matching the name.
                     If empty, fetches all schemes.

    Returns:
        A JSON string containing a list of schemes, each with its full set of criteria
        (min_age, max_income, community, etc.) for the agent to analyze.
    """
    import sqlite3
    import json
    import os
    from dotenv import load_dotenv

    load_dotenv()
    DB_PATH = os.getenv("SCHEMES_DB_PATH", "karnataka_schemes.db")

    if not os.path.exists(DB_PATH):
        return json.dumps({"error": "Database file not found."})

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # The SELECT statement now fetches ALL criteria columns for the agent to use.
    base_query = """
        SELECT
            s.id, s.name, d.name as department_name, s.definition,
            s.eligibility_summary, s.application_fee, s.required_information, s.supporting_documents,
            s.min_age, s.max_age, s.gender_eligibility, s.max_annual_income, s.community_eligibility,
            s.declaration_text, sg.district
        FROM schemes s
        JOIN departments d ON s.department_id = d.id
        JOIN scheme_geographies sg ON s.id = sg.scheme_id
    """
    params = []
    
    if scheme_name:
        query = f"{base_query} WHERE s.name LIKE ? GROUP BY s.id"
        params.append(f"%{scheme_name}%")
    else:
        # If no specific name, fetch ALL schemes.
        query = f"{base_query} GROUP BY s.id"

    cursor.execute(query, params)
    schemes_raw = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Process JSON fields before returning
    for scheme in schemes_raw:
        scheme['required_information'] = json.loads(scheme.get('required_information') or '[]')
        scheme['supporting_documents'] = json.loads(scheme.get('supporting_documents') or '[]')
        scheme['community_eligibility'] = json.loads(scheme.get('community_eligibility') or '[]')


    if not schemes_raw:
        return json.dumps({"message": "No schemes found."})
    
    return json.dumps(schemes_raw)

async def generate_application_pdf(application_data_json: str, application_id: str) -> str:
    """
    Generates a PDF, reads it as a BLOB, and then UPDATES the existing application
    record in the database to store this BLOB.

    Args:
        application_data_json: A JSON string of all collected application information.
        application_id: The unique UUID of the application record to update, which was
                        generated by the save_application tool.

    Returns:
        A JSON string confirming that the PDF was generated and attached to the record.
    """
    import sqlite3
    import json
    import os
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.enums import TA_LEFT

    DB_PATH = os.getenv("APPLICATION_DB_PATH")

    def flatten_nested_data(data_dict, parent_key='', separator=' - '):
        """Helper function to flatten nested dictionary."""
        flattened = {}
        for key, value in data_dict.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key
            if isinstance(value, dict):
                flattened.update(flatten_nested_data(value, new_key, separator))
            elif isinstance(value, list):
                if all(isinstance(item, str) for item in value):
                    flattened[new_key] = ", ".join(value)
                else:
                    for i, item in enumerate(value, 1):
                        flattened[f"{new_key} {i}"] = str(item)
            else:
                flattened[new_key] = value
        return flattened

    filename = f"{application_id}.pdf"
    pdf_blob = None

    try:
        # Step 1: Generate the PDF and save it temporarily
        data_dict = json.loads(application_data_json)
        flattened_data = flatten_nested_data(data_dict)
        
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        c.setTitle("Application Information")
        
        styles = getSampleStyleSheet()
        style_label = styles['BodyText']
        style_label.fontName = 'Helvetica-Bold'
        style_value = styles['BodyText']
        style_value.alignment = TA_LEFT
        
        heading_text = "Application Details"
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width / 2.0, height - 40, heading_text)
        
        y_position = height - 80
        x_label = 50
        x_value = 220
        entry_spacing = 15

        c.setFont("Helvetica-Bold", 12)
        c.drawString(x_label, y_position, "Application ID:")
        c.setFont("Helvetica", 12)
        c.drawString(x_value, y_position, application_id)
        y_position -= 40

        for key, value in flattened_data.items():
            formatted_key = key.replace('_', ' ').replace(' - ', ' ').title() + ':'
            value_str = str(value)
            
            label_p = Paragraph(formatted_key, style_label)
            value_p = Paragraph(value_str, style_value)
            
            label_available_width = x_value - x_label - 10
            value_available_width = width - x_value - 50
            
            label_p.wrapOn(c, label_available_width, height)
            value_w, value_h = value_p.wrap(value_available_width, height)
            
            entry_height = max(label_p.height, value_h)
            
            if y_position - entry_height < 60:
                c.showPage()
                y_position = height - 60
            
            y_position -= entry_height
            
            label_p.drawOn(c, x_label, y_position)
            value_p.drawOn(c, x_value, y_position)
            
            y_position -= entry_spacing
            
        c.save()

        # Step 2: Read the temporary file into a binary BLOB
        with open(filename, 'rb') as f:
            pdf_blob = f.read()

        # Step 3: UPDATE the existing database record with the BLOB
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE applications SET application_pdf = ? WHERE application_id = ?",
            (pdf_blob, application_id)
        )
        conn.commit()
        conn.close()

        # Step 4: Delete the temporary PDF file
        if os.path.exists(filename):
            os.remove(filename)

        return {"filename": filename}

    except Exception as e:
        return json.dumps({"status": "Error", "error": f"Failed to generate and attach PDF: {str(e)}"})

import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
import os

import sqlite3
from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.getenv("APPLICATION_DB_PATH")
 
def generate_filled_application_pdf(application_data: dict, application_id: str, scheme_name:str):
    """
    Fill a bilingual PDF form based on scheme name with hardcoded defaults
 
    Args:
        application_data (dict): Dictionary containing field values provided by user
        scheme_name (str): Name of the scheme ("Bus Pass" or "Self Employment Loan")
        output_filename (str, optional): Custom output filename
    """
    output_filename=None
 
    scheme_config = {
        "Application for Issue of Bus Passes to Physically Challenged": {
            "template": os.path.join("pdf_templates","bus_pass_application.pdf"),
            "layout": os.path.join("pdf_templates","bus_pass_application_layout.json"),
            "default_output": f"{application_id}.pdf"
        },
        "Self-Employment Scheme": {
            "template": os.path.join("pdf_templates","self_employment_loan_application.pdf"),
            "layout": os.path.join("pdf_templates","self_employment_loan_application_layout.json"),
            "default_output": f"{application_id}.pdf"
        },
        "application of Renewal of Bus Passes to Physically Challenged": {
            "template": os.path.join("pdf_templates","bus_pass_renewal_application.pdf"),
            "layout": os.path.join("pdf_templates","bus_pass_renewal_layout.json"),
            "default_output": f"{application_id}.pdf"
        },
        "Application for Senior Citizen Card": {
            "template": os.path.join("pdf_templates","senior_citizen_card_application.pdf"),
            "layout": os.path.join("pdf_templates","senior_citizen_card_application_layout.json"),
            "default_output": f"{application_id}.pdf"
        }
    }
 
    scheme_key = None
    for key in scheme_config.keys():
        if scheme_name.lower().replace(" ", "").replace("_", "") == key.lower().replace(" ", "").replace("_", ""):
            scheme_key = key
            break
 
    if not scheme_key:
        available_schemes = list(scheme_config.keys())
        raise ValueError(f"Unknown scheme: '{scheme_name}'. Available schemes: {available_schemes}")
 
    config = scheme_config[scheme_key]
 
    final_fields = apply_hardcoded_defaults(scheme_key, application_data)
 
    print(f"Processing scheme: {scheme_key}")
    print(f"Template: {config['template']}")
    print(f"Layout: {config['layout']}")
    print(f"Output: {output_filename or config['default_output']}")
    print(f"Applied hardcoded defaults for missing fields")
 
    return process_bilingual_pdf(
        template_pdf=config["template"],
        layout_json=config["layout"],
        output_pdf=output_filename or config["default_output"],
        field_values=final_fields,
        application_id=application_id
    )
 
def apply_hardcoded_defaults(scheme_name, user_fields):
    """
    Apply hardcoded defaults for missing fields based on scheme type
 
    Args:
        scheme_name (str): Name of the scheme
        user_fields (dict): Fields provided by user
 
    Returns:
        dict: Complete fields dictionary with defaults applied
    """
 
    final_fields = user_fields.copy()
 
    if scheme_name == "Application for Issue of Bus Passes to Physically Challenged":
        scheme_defaults = {
            "Declaration Agree": True,
            "Temporary Address": "Same as permanent address",
        }
    elif scheme_name == "Self-Employment Scheme":
        scheme_defaults = {
            "Declaration Agree": True,
            "domicile": "Karnataka",
            "Financial Year": "2025-26"
        }
    elif scheme_name == "Application for Senior Citizen Card":
        scheme_defaults = {
            "Declaration Agree": "I Agree",
            "domicile": "Karnataka",
            "Financial Year": "2025-26"
        }
    elif scheme_name == "application of Renewal of Bus Passes to Physically Challenged":
        scheme_defaults = {
            "Declaration Agree": True,
            "Temporary Address": "Same as permanent address",
        }
    else:
        scheme_defaults = {}
 
    for key, default_value in {**scheme_defaults}.items():
        if key not in final_fields:
            final_fields[key] = default_value
            print(f"  ✓ Applied default: {key} = {default_value}")
 
    if scheme_name == "Self-Employment Scheme":
        gender_fields = ["gender_male", "gender_female", "gender_others"]
 
        if "gender" in final_fields:
            gender_value = str(final_fields["gender"]).lower()
            for gf in gender_fields:
                final_fields[gf] = False
 
            if gender_value in ["male", "m", "ಪುರುಷ"]:
                final_fields["gender_male"] = True
            elif gender_value in ["female", "f", "ಮಹಿಳೆ"]:
                final_fields["gender_female"] = True
            else:
                final_fields["gender_others"] = True
 
            print(f"  ✓ Converted gender '{final_fields['gender']}' to checkboxes")
 
    return final_fields
 
 
def process_bilingual_pdf(template_pdf, layout_json, output_pdf, field_values, application_id):
    """
    Process the bilingual PDF with proper Kannada font support and alignment,
    then save it into the database as a BLOB, and finally remove the temp file.
    """
 
    try:
        pdfmetrics.registerFont(TTFont('NotoKannada', 'NotoSansKannada-Regular.ttf'))
        kannada_font = 'NotoKannada'
        print("✓ Using Noto Sans Kannada font for proper text display")
    except:
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
            kannada_font = 'DejaVuSans'
            print("! Using DejaVu Sans font - may not display all Kannada characters properly")
        except:
            kannada_font = 'Helvetica'
            print("⚠ Warning: Using Helvetica - Kannada text will not display properly")
            print("Please download NotoSansKannada-Regular.ttf for proper Kannada support")
 
    with open(layout_json, "r", encoding='utf-8') as f:
        layout = json.load(f)
 
    pages_with_fields = set(fld["page"] for fld in layout)
    overlay_files = {}
 
    for page_num in pages_with_fields:
        overlay_filename = f"overlay_page_{page_num}.pdf"
        c = canvas.Canvas(overlay_filename, pagesize=A4)
        width, height = A4
 
        for fld in layout:
            if fld["page"] == page_num:
                name = fld["field"]
                if name in field_values:
                    x = fld["x"]
                    y = fld["y"]
                    font_size = fld.get("font_size", 10)
                    text = str(field_values[name])
 
                    if fld.get("type") == "checkbox" and field_values[name]:
                        c.setFont("Helvetica", font_size)
                        c.drawString(x, y, "✓")
                    elif fld.get("type") != "checkbox":
                        has_kannada = any(0x0C80 <= ord(char) <= 0x0CFF for char in text)
 
                        if has_kannada:
                            c.setFont(kannada_font, font_size)
                            print(f"✓ Using Kannada font for field '{name}': {text}")
                        else:
                            c.setFont("Helvetica", font_size)
 
                        multiline_fields = ["address", "purpose_of_loan", "permanent_address",
                                            "temporary_address", "division_details"]
 
                        if any(field in name.lower() for field in multiline_fields) and len(text) > 45:
                            lines = wrap_text(text, 45)
                            for i, line in enumerate(lines[:3]):
                                line_y = y - (i * 12)
                                c.drawString(x, line_y, line)
                        else:
                            if len(text) > 50:
                                text = text[:47] + "..."
                            c.drawString(x, y, text)
 
        c.save()
        overlay_files[page_num] = overlay_filename
 
    try:
        reader_base = PdfReader(template_pdf)
        writer = PdfWriter()
 
        for page_index in range(len(reader_base.pages)):
            page_num = page_index + 1
            page_base = reader_base.pages[page_index]
 
            if page_num in overlay_files:
                try:
                    overlay_reader = PdfReader(overlay_files[page_num])
                    page_overlay = overlay_reader.pages[0]
                    page_base.merge_page(page_overlay)
                except Exception as e:
                    print(f"Warning: Could not merge overlay for page {page_num}: {e}")
 
            if "/Annots" in page_base:
                del page_base["/Annots"]
 
            writer.add_page(page_base)
 
        # Save temp file first
        with open(output_pdf, "wb") as out_f:
            writer.write(out_f)
 
        print(f"✓ Bilingual PDF generated successfully: {output_pdf}")
 
        # --- STEP 2: Read PDF into binary BLOB ---
        with open(output_pdf, "rb") as f:
            pdf_blob = f.read()
 
        # --- STEP 3: Update DB record ---
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE applications SET application_pdf = ? WHERE application_id = ?",
            (pdf_blob, application_id)
        )
        conn.commit()
        conn.close()
        print(f"✓ PDF saved into database for application_id={application_id}")
 
    except Exception as e:
        print(f"Error creating PDF: {e}")
    finally:
        # --- STEP 4: Cleanup temp overlay + output file ---
        for overlay_file in overlay_files.values():
            if os.path.exists(overlay_file):
                os.remove(overlay_file)
        if os.path.exists(output_pdf):
            os.remove(output_pdf)
            print(f"✓ Temporary PDF file deleted: {output_pdf}")
 
 
def wrap_text(text, max_chars_per_line):
    """Intelligently wrap text to fit within specified character limit"""
    words = text.split()
    lines = []
    current_line = ""
 
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if len(test_line) <= max_chars_per_line:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
 
    if current_line:
        lines.append(current_line)
 
    return lines

if __name__ == "__main__":
    generate_filled_application_pdf(
        application_data={},
        application_id="KN-20250918-113603-8746",
        scheme_name="Application for Issue of Bus Passes to Physically Challenged"
    )