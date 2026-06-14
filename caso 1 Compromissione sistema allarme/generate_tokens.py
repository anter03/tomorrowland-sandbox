import jwt
import time

SECRET_KEY = "chiave_segreta_del_festival"

# 1. Valid Admin Token (role: admin, valid exp in future)
payload_valid_admin = {
    "role": "admin",
    "exp": int(time.time()) + 3600
}
token_valid_admin = jwt.encode(payload_valid_admin, SECRET_KEY, algorithm="HS256")

# 2. Expired Admin Token (role: admin, exp in past)
payload_expired_admin = {
    "role": "admin",
    "exp": int(time.time()) - 3600
}
token_expired_admin = jwt.encode(payload_expired_admin, SECRET_KEY, algorithm="HS256")

# 3. Low Privilege Token (role: user, valid exp in future)
payload_low_priv = {
    "role": "user",
    "exp": int(time.time()) + 3600
}
token_low_priv = jwt.encode(payload_low_priv, SECRET_KEY, algorithm="HS256")

# 4. Invalid Token (wrong secret key)
token_invalid_sig = jwt.encode(payload_valid_admin, "wrong_secret_key", algorithm="HS256")

print("--- GENERATED TOKENS FOR TESTING ---")
print(f"1. Valid Admin Token:\n{token_valid_admin}\n")
print(f"2. Expired Admin Token:\n{token_expired_admin}\n")
print(f"3. Low Privilege Token:\n{token_low_priv}\n")
print(f"4. Invalid Signature Token:\n{token_invalid_sig}\n")
