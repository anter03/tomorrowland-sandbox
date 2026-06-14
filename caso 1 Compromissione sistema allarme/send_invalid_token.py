import jwt
import time
import urllib.request
import json

SECRET_KEY = "chiave_segreta_del_festival"
URL = "http://localhost:5000/api/broadcast"

# Genera un token non valido (ruolo admin, scadenza passata / scaduto)
payload = {
    "role": "admin",
    "exp": int(time.time()) - 3600
}
token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

headers = {
    "X-Admin-Token": token,
    "Content-Type": "application/json"
}
body = {
    "message": "ATTENZIONE: Evacuazione immediata stage!"
}
data = json.dumps(body).encode("utf-8")

req = urllib.request.Request(URL, data=data, headers=headers, method="POST")

print(f"Invio richiesta a {URL}...")
print(f"Token utilizzato (Non Valido - Scaduto):\n{token}\n")

try:
    with urllib.request.urlopen(req) as response:
        print(f"HTTP Status: {response.status}")
        print("Risposta dal server:")
        print(json.dumps(json.loads(response.read().decode("utf-8")), indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print("Risposta di errore dal server:")
    print(json.dumps(json.loads(e.read().decode("utf-8")), indent=2))
except Exception as e:
    print(f"Errore di connessione: {e}")
