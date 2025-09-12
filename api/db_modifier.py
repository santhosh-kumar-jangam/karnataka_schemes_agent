import sqlite3

conn = sqlite3.connect(r"C:\Users\Santhosh\Desktop\gov schemes agent new\api\applications.db")
cursor = conn.cursor()
cursor.execute("ALTER TABLE applications ADD COLUMN application_pdf BLOB")
conn.commit()
conn.close()