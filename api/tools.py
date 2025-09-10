def save_application(app_uuid: str, scheme_name: str, aadhar_number: str, applicant_name: str, phone: str) -> dict:
    """
    Save a new scheme application into the database.

    Args:
        app_uuid (str): Application ID (uuid)
        scheme_name (str): Name of the scheme applied for
        aadhar_number (str): User's Aadhaar number
        applicant_name (str): Name of the applicant
        phone (str): Phone number of the applicant

    Returns:
        dict: {"application_uuid": str, "status": str}
    """
    import sqlite3, os

    from dotenv import load_dotenv
    load_dotenv()

    DB_PATH = os.getenv("APPLICATION_DB_PATH")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO applications (application_uuid, scheme_name, aadhar_number, applicant_name, phone)
        VALUES (?, ?, ?, ?, ?)
        """, (app_uuid, scheme_name, aadhar_number, applicant_name, phone)
    )

    conn.commit()
    conn.close()

    return {"application_uuid": app_uuid, "status": "Submitted"}

def check_application_status(application_uuid: str) -> dict:
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
    
def calculate_age(dob_str):
    from datetime import datetime, date
    born = datetime.strptime(dob_str, "%Y-%m-%d").date()
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def fetch_user_profile(aadhaar_number: str) -> str:
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
        user_dict['age'] = calculate_age(user_dict['dob'])
        return json.dumps(user_dict)
    else:
        return json.dumps({"error": "No user profile found for the provided Aadhaar number."})
    

def find_eligible_schemes(user_profile_json: str = "{}", scheme_name: str = "") -> str:
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
                    params.extend([profile['age'], profile['age']])
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