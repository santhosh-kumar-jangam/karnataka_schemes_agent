import sqlite3
import json
import os

DB_FILE = "karnataka_schemes.db"

schemes_data = [
  {
    "id": 804,
    "name": "Application for Issue of Bus Passes to Physically Challenged",
    "department_id": 76,
    "definition": "This service is for application of free bus pass by a physically challenged person",
    "procedure": [
      "Applicant logs into Seva Sindhu portal.",
      "Applicant provides the user credentials provided by Drugs Control Department to apply for this service",
      "Applicant submits the application on Seva Sindhu portal along with necessary supporting documents and makes the payment for the service.",
      "Applicant to provide clarification through re-submission of documents if requested by the Department",
      "The approving authority approves and applicant collects the digitally signed certificate or the approving authority rejects and applicant collects the endorsement stating reasons for rejection."
    ],
    "documents": [
      "Disability certificate",
      "I.D card issued by Directorate for the Empowerment of Differently abled and Seniro Citizens.",
      "Address proof (voter ID, aadhar card, ration card)",
      "Passport size photo",
    ],
    "required_information": [
      "Applicant Full Name",
      "father name",
      "Aadhaar Number",
      "Phone Number",
      "Category (SC, ST, OBC, General)",
      "Type of employment ('employee of govt organization' or 'Not an employee of govt organization' or 'Employee of Semi-govt organization' or 'Not an employee of Semi-govt organization' )",
      "Disability Certificate / UDID Card Number (18 digit)",
      "Type of disability (Hearing, Walking etc)",
      "Disability percentage (40 percent or above)",
      "Pass issuing division",
      "Permanant Address",
      "Temporary Address",
      "Medical certificate number"
    ],
    "benefit_type": "Service",
    "max_benefit_amount": 0.0,
    "interest_rate": 0.0,
    "min_age": 0,
    "max_age": 99,
    "gender": "Any",
    "max_income": 9999999.0,
    "community": [
      "Disability"
    ],
    "fee": 25.0,
    "eligibility": "Physically challenged"
  },
  {
    "id": 1931,
    "name": "application of Renewal of Bus Passes to Physically Challenged",
    "department_id": 76,
    "definition": "This service is an application for Renewal of us pass for Physically Challenged",
    "procedure": [
      "Applicant logs into Seva Sindhu portal.",
      "Applicant provides the user credentials provided by Drugs Control Department to apply for this service",
      "Applicant submits the application on Seva Sindhu portal along with necessary supporting documents and makes the payment for the service.",
      "Applicant to provide clarification through re-submission of documents if requested by the Department",
      "The approving authority approves and applicant collects the digitally signed certificate or the approving authority rejects and applicant collects the endorsement stating reasons for rejection"
    ],
    "documents": [
      "Disability certificate",
      "I.D card issued by Directorate for the Empowerment of Differently abled and Seniro Citizens.",
      "Proof of Residential Address",
      "Passport size photo"
    ],
    "required_information": [
      "Applicant Full Name",
      "age",
      "gender",
      "guardian or father name",
      "date of birth",
      "Aadhaar Number",
      "Phone Number",
      "Disability Certificate / UDID Card Number",
      "Residential Address",
      "Previous Bus Pass Number"
    ],
    "benefit_type": "Service",
    "max_benefit_amount": 0.0,
    "interest_rate": 0.0,
    "min_age": 0,
    "max_age": 99,
    "gender": "Any",
    "max_income": 9999999.0,
    "community": [
      "Disability"
    ],
    "fee": 25.0,
    "eligibility": "Physically challenged"
  },
  {
    "id": 61,
    "name": "Application for Senior Citizen Card",
    "department_id": 15,
    "definition": "Application for issuance of senior citizen card. This card can be used for availing various concessions and exemptions applicable to senior citizens.",
    "procedure": [
      "Application submission (Online, B1/K1 centres, CSC centres)",
      "The application is routed to the Programme Assistant at the respective district",
      "Verification by the Programme Assistant. Recommendations of the Programme Assistant are sent to the District Disabled Welfare Officer (DDWO) for review",
      "Verification by the DDWO. Approve or reject the application request"
    ],
    "documents": [
      "Age proof",
      "Address proof (voter ID, aadhar card, ration card)",
    ],
    "required_information": [
      "Applicant Full Name",
      "Aadhaar Number",
      "Date of Birth",
      "district",
      "taluk",
      "pincode",
      "Full Residential Address",
      "gender",
      "age",
      "Phone Number for Communication"
    ],
    "benefit_type": "Service",
    "max_benefit_amount": 0.0,
    "interest_rate": 0.0,
    "min_age": 60,
    "max_age": 99,
    "gender": "Any",
    "max_income": 9999999.0,
    "community": [
      "Senior Citizen",
      "General"
    ],
    "fee": 20.0,
    "eligibility": "The applicant must be at least 60 years of age. The applicant must be a resident of Karnataka"
  },
  {
    "id": 51,
    "name": "Self-Employment Scheme",
    "department_id": 1150,
    "definition": "Under this scheme, loans and subsidy will be provided to the religious minority communities with the help of Nationalized / Scheduled banks to start or improve a small-scale handicraft industry, service sector and agro-based activities. 33% of the unit cost or maximum of Rs. 1.00 Lakh will be given as a subsidy.",
    "procedure": [
      "Applicant submits an online application with all required documents and project report.",
      "The application is reviewed by the District Officer for eligibility and completeness.",
      "The application is forwarded to the selected bank for loan sanctioning.",
      "Upon bank approval, the subsidy is released by KMDC and the loan is disbursed by the bank."
    ],
    "documents": [
      "latest passport size photo",
      "Caste certificate",
      "income certificate",
      "ration card",
      "Aadhaar card",
      "passbook"
    ],
    "required_information": [
      "Applicant Full Name",
      "Aadhaar Number",
      "Phone Number for Communication",
      "Date of Birth",
      "Category (SC/ST)"
      "Caste Certificate RD Number",
      "caste name",
      "Income Certificate RD Number",
      "Ration Card",
      "district",
      "taluk",
      "hobli",
      "village",
      "assembly constituency name",
      "Full Residential Address",      
      "Details of the proposed business/activity",
      "Loan Amount Requested",
      "Declaration of no prior KMDC loan",
      "Declaration of no government employee in the family"
    ],
    "benefit_type": "Loan with Subsidy",
    "max_benefit_amount": 100000.0,
    "interest_rate": 0.0,
    "min_age": 18,
    "max_age": 55,
    "gender": "Any",
    "max_income": 600000.0,
    "community": [
      "Minority"
    ],
    "fee": 0.0,
    "eligibility": "Applicant must belong to a State Religious Minority Community (SC or ST only) and be a permanent resident of the State. Age must be between 18 to 55 years. Annual family income should not exceed Rs. 6.00 lakh. No family member should be a government/PSU employee, and the applicant must not have availed a previous loan from KMDC."
  }
]

# 2. Departments inferred from the schemes above
departments_data = [
    {'id': 76, 'name': 'Transport Department', 'state': 'Karnataka'},
    {'id': 15, 'name': 'Department for Empowerment of Differently Abled and Senior Citizens', 'state': 'Karnataka'},
    {'id': 1150, 'name': 'Karnataka Minorities Development Corporation (KMDC)', 'state': 'Karnataka'},
]

# 3. Geography mappings for all four schemes
geographies_data = [
    {'scheme_id': 804, 'state': 'Karnataka', 'district': 'All Districts'},
    {'scheme_id': 1931, 'state': 'Karnataka', 'district': 'All Districts'},
    {'scheme_id': 61, 'state': 'Karnataka', 'district': 'All Districts'},
    {'scheme_id': 51, 'state': 'Karnataka', 'district': 'All Districts'},
]


def create_new_database():
    """Creates a new database file from scratch with the specified schemes."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Removed existing database file: {DB_FILE}")

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print("Creating database tables...")

        # Create Tables with schema matching the template
        cursor.execute('''CREATE TABLE departments (id INT PRIMARY KEY, name VARCHAR(255) NOT NULL, state VARCHAR(100))''')
        cursor.execute('''
            CREATE TABLE schemes (
                id INT PRIMARY KEY, name VARCHAR(255) NOT NULL, department_id INT,
                definition TEXT, procedure JSON, supporting_documents JSON, required_information JSON,
                benefit_type VARCHAR(100), max_benefit_amount REAL, interest_rate REAL,
                min_age INT, max_age INT, gender_eligibility VARCHAR(50), max_annual_income REAL,
                community_eligibility JSON, application_fee REAL, eligibility_summary TEXT,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )''')
        cursor.execute('''
            CREATE TABLE scheme_geographies (
                id INTEGER PRIMARY KEY AUTOINCREMENT, scheme_id INT NOT NULL,
                state VARCHAR(100), district VARCHAR(100),
                FOREIGN KEY (scheme_id) REFERENCES schemes(id)
            )''')
        
        print("Populating tables...")
        # Populate Departments
        for dept in departments_data:
            cursor.execute("INSERT OR IGNORE INTO departments (id, name, state) VALUES (?, ?, ?)",
                           (dept['id'], dept['name'], dept['state']))

        # Populate Schemes
        for scheme in schemes_data:
            cursor.execute("""
                INSERT INTO schemes (
                    id, name, department_id, definition, procedure, supporting_documents,
                    required_information, benefit_type, max_benefit_amount, interest_rate, min_age,
                    max_age, gender_eligibility, max_annual_income, community_eligibility,
                    application_fee, eligibility_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scheme['id'], scheme['name'], scheme['department_id'], scheme['definition'],
                json.dumps(scheme['procedure']), json.dumps(scheme['documents']),
                json.dumps(scheme['required_information']), scheme['benefit_type'],
                scheme['max_benefit_amount'], scheme['interest_rate'], scheme['min_age'],
                scheme['max_age'], scheme['gender'], scheme['max_income'],
                json.dumps(scheme['community']), scheme['fee'], scheme['eligibility']
            ))

        # Populate Geographies
        for geo in geographies_data:
            cursor.execute("INSERT INTO scheme_geographies (scheme_id, state, district) VALUES (?, ?, ?)",
                           (geo['scheme_id'], geo['state'], geo['district']))

        conn.commit()
        print(f"\nSuccessfully created new database '{DB_FILE}' with {len(schemes_data)} schemes.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    create_new_database()