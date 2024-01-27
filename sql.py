import sqlite3

conn = sqlite3.connect('items.db')
conn.execute('UPDATE items SET user_id = 1 WHERE user_id IS NULL')
conn.commit()
conn.close()
print('Update successful')

