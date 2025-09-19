import sqlite3

conn = sqlite3.connect(r"C:\Users\Santhosh\Desktop\gov schemes agent new\api\databases\karnataka_schemes.db")
cursor = conn.cursor()
cursor.execute("""
delete from schemes where id=61
""")
conn.commit()
conn.close()