from cryptography.fernet import Fernet
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
print("Starting db update")

# encryption_key = b'5gP6PJiet87ZyOYda17lzFemrpK3bGk3f5zLm5nZsBU='
# cipher_suite = Fernet(encryption_key)
# openai_api_key = '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'
# encrypted_api_key = cipher_suite.encrypt(openai_api_key.encode())
# print(encrypted_api_key)

# username = "chefSohee"
# password = "yiw43wu90iv9"
# password_hash = generate_password_hash(password)

# conn = sqlite3.connect('items.db')
# conn.execute("INSERT INTO users (username,password_hash,openai_api_key) VALUES (?, ?, ?)", (username,password_hash,encrypted_api_key))
# print(username,generate_password_hash,encrypted_api_key)
# conn.commit()

# conn.close()