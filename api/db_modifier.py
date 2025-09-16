import sqlite3

conn = sqlite3.connect(r"C:\Users\Santhosh\Desktop\gov schemes agent new\api\databases\karnataka_schemes.db")
cursor = conn.cursor()
cursor.execute("""
UPDATE schemes SET required_information='["Applicant Full Name",
  "age",
  "father name",
  "gender",
  "guardian or father name",
  "date of birth",
  "Category (SC, ST, OBC, General)",
  "Aadhaar Number",
  "Phone Number",
  "Disability Certificate / UDID Card Number",
  "Pass issuing division (''Bellary'' or ''Bidar''or ''Hospet''or ''Kalburgi''or ''Koppal''or ''Raaichur''or ''Vijaypura''or ''Yadgir'')",
  "Permanant Address",
  "Temporary Address",
  "Previous Bus Pass Number"
]'
  WHERE id=1931;
""")
conn.commit()
conn.close()