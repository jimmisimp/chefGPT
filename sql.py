import sqlite3

conn = sqlite3.connect('items.db')
conn.execute('ALTER TABLE items ADD COLUMN tags TEXT')
conn.close()
print("Completed")
