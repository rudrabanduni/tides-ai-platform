import sqlite3
conn = sqlite3.connect('tides_ai.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())
cursor.execute("SELECT * FROM api_keys LIMIT 5;")
print("API Keys:", cursor.fetchall())
conn.close()
