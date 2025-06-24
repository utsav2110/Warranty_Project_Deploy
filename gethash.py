import bcrypt
print(bcrypt.hashpw("your_password".encode(), bcrypt.gensalt()).decode())