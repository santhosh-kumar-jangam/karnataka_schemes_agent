import sqlite3

conn = sqlite3.connect(r"C:\Users\Santhosh\Desktop\gov schemes agent new\api\databases\applications.db")
cursor = conn.cursor()
cursor.execute("DELETE FROM applications;")
conn.commit()
conn.close()