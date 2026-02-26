import sqlite3

DBNAME = "chatbot.db"

conn = sqlite3.connect(DBNAME)
cursor = conn.cursor()

cursor.execute("DELETE FROM checkpoints")
cursor.execute("DELETE FROM writes")

conn.commit()
conn.close()

print("✅ Database cleaned successfully")
