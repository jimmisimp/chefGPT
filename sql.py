import sqlite3


# Your encrypted key as a raw string
encrypted_key = b"gAAAAABltZkdQRcFL72hSk6ABPCkv1yz7Gn7KEnY-fHvWVxKqzFp16KZKYy1CQ-jJqbeHTl9OULqVxdN02drbm8PzCVGQOeoNzquwO39ATHzpdlOalyKP6r-k24diydHHM0cfjvEY7pFKIMYW56qKg-ZfFrT4tl9Ug=="

# Connect to the database
conn = sqlite3.connect('items.db')

# Execute the update with parameter substitution
conn.execute("UPDATE users SET openai_api_key = ?", (encrypted_key,))
conn.commit()

# Close the connection
conn.close()

print('Update successful')

