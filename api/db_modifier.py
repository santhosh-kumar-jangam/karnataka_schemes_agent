import sqlite3

conn = sqlite3.connect(r"C:\Users\Santhosh\Desktop\gov schemes agent\api\applications.db")
cursor = conn.cursor()
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS applications (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     application_uuid TEXT UNIQUE NOT NULL,
#     scheme_name TEXT NOT NULL,
#     aadhar_number TEXT NOT NULL,
#     applicant_name TEXT,
#     phone TEXT,
#     status TEXT DEFAULT 'Submitted',
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# )
# """)
cursor.execute("DELETE FROM applications")
conn.commit()
conn.close()