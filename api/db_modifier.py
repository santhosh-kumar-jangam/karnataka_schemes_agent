import sqlite3

conn = sqlite3.connect(r"C:\Users\Santhosh\Desktop\gov schemes agent new\api\databases\karnataka_schemes.db")
cursor = conn.cursor()
cursor.execute("""
UPDATE schemes SET required_information='["Applicant Full Name",
  "Aadhaar Number",
  "Phone Number for Communication",
  "Date of Birth",
  "Category (SC/ST)",
  "Caste Certificate RD Number",
  "Corporation (Karnataka Maharishi Valmiki Scheduled Tribe Development Corporation LTD or Karnataka Medara Scheduled Tribe Nomadic Development Corporation)",
  "caste name",
  "Annual Income (MAX 1.5 Lakh for Rural and 2 Lakh for Urban)",
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
]'
  WHERE id=51;
""")
conn.commit()
conn.close()