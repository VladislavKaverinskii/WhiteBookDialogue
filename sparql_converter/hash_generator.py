import os
import hashlib

# password = "rksor6fj82g2gdj31gj"
password = "fkwv47gs2j03cs5r"

salt = os.urandom(32)
key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

print ("salt: ", salt)
print()
print("key", key)
