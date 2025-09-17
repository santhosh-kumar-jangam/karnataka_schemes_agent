import sqlite3

conn = sqlite3.connect(r"C:\Users\Santhosh\Desktop\gov schemes agent new\api\databases\user_details.db")
cursor = conn.cursor()
cursor.execute("""
INSERT INTO user_details 
(full_name, dob, gender, aadhaar_number, current_address, permanent_address, district, state, pincode, ration_card_id, caste_certificate_rd, income_certificate_rd, community, annual_income)
VALUES
("Vishnu", "2005-11-09", "Male", "814350858746", "S/O: babbanna, mittimalkapur, raichur", "S/O: babbanna, mittimalkapur, raichur", "Raichur", "Karnataka", "584103", "520400193566", "RD0038186129648", "RD0038026261703", "General", "100000"),
("Mohammad Fazil", "1999-11-03", "Male", "906748279705", "S/O: abdul, matt road, maseedikere, B.kanabur", "S/O: abdul, matt road, maseedikere, B.kanabur", "chickmagalur", "Karnataka", "577112", "520200406038", "RD073783379648", "RD0038026261703", "General", "90000"),
("Sowmya R", "1995-07-14", "Female", "488676008935", "D/O: ramesh b k, #84,6th cross, kuvempunagara", "D/O: ramesh b k, #84,6th cross, kuvempunagara", "shimoga", "Karnataka", "577451", "520200532686", "RD078786843848", "RD0038026261703", "General", "87000")
""")
conn.commit()
conn.close()