from cryptography.fernet import Fernet
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# encryption_key = b'5gP6PJiet87ZyOYda17lzFemrpK3bGk3f5zLm5nZsBU='
# cipher_suite = Fernet(encryption_key)
# openai_api_key = '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'
# encrypted_api_key = cipher_suite.encrypt(openai_api_key.encode())
# print(encrypted_api_key)

# print("Starting db update")

# encrypted_key = b'gAAAAABluA62XWiJH-TiyQxUEeLP3t6w2QHcWt_p6asszSGP7EkCV987G-woX7ZUsAjP_lqUCm09XtKqTC3K2vXfw5sYpQP4PsWZBkgXxTAo3PwlwPUSgoKRmgzlRcV3oKyj5kgc-c_4VWPQHJxbYQJg-MkbAhIZrg=='

# password = "ox35vl9ys3jy"
# password_hash = generate_password_hash(password)

# conn = sqlite3.connect('items.db')
# # Execute the update with parameter substitution
# conn.execute("INSERT INTO users (username,password_hash,openai_api_key) VALUES (?, ?, ?)", ("chefStep",password_hash,encrypted_key))
# conn.commit()

# # Close the connection
# conn.close()

# print("chefSteph",generate_password_hash,encrypted_key)
conn = sqlite3.connect('items.db')
conn.execute("UPDATE users SET username = 'chefStef' WHERE username = chefSteph")
conn.commit()

# Close the connection
conn.close()