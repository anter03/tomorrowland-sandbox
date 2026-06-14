import logging
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
os.makedirs('/var/log/tomorrowland', exist_ok=True)
logging.basicConfig(filename='/var/log/tomorrowland/cyber_dashboard.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SECURITY_MODE = os.environ.get('SECURITY_MODE', 'VULNERABLE')
STAFF_DB = {"m.rossi@tomorrowland.com": "cashless2026"}
failed_attempts = {}

# 1. AUTENTICAZIONE (Vulnerabile al Brute Force)
@app.route('/api/v1/staff/auth', methods=['POST'])
def login():
    global failed_attempts
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    
    if SECURITY_MODE == "SECURE" and failed_attempts.get(username, 0) >= 3:
        logging.warning("SECURITY_ENFORCEMENT: Account bloccato per Brute Force")
        return jsonify({"status": "error", "message": "Too Many Requests - Account Temporaneamente Bloccato"}), 429
    
    if username in STAFF_DB and STAFF_DB[username] == password:
        if SECURITY_MODE == "SECURE":
            failed_attempts[username] = 0
            return jsonify({"status": "MFA_REQUIRED", "message": "Inserire OTP"}), 200
        else:
            logging.info(f"AUTH_SUCCESS: {username} è entrato nella Dashboard Crowd AI.")
            return jsonify({"token": "JWT_ADMIN_VALIDO_12345", "role": "Crowd_Manager"}), 200
    else:
        if SECURITY_MODE == "SECURE":
            failed_attempts[username] = failed_attempts.get(username, 0) + 1
        logging.warning(f"AUTH_FAIL: Tentativo di accesso fallito per {username} dall'IP {request.remote_addr}")
        return jsonify({"status": "error", "message": "Credenziali errate"}), 401

@app.route('/api/v1/staff/auth/mfa', methods=['POST'])
def verify_mfa():
    data = request.json
    username = data.get('username', '')
    otp = data.get('otp', '')
    
    if username in STAFF_DB:
        if otp == "123456":  # Simulazione di un codice OTP valido
            logging.info(f"MFA_SUCCESS: {username} ha superato la verifica OTP.")
            return jsonify({"token": "JWT_ADMIN_VALIDO_12345", "role": "Crowd_Manager"}), 200
        else:
            logging.warning(f"MFA_FAIL: Tentativo OTP fallito per {username}")
            return jsonify({"status": "error", "message": "OTP non valido"}), 401
    return jsonify({"status": "error", "message": "Utente non trovato"}), 404

# 2. ACCESSO AI DATI RFID (Simula il furto dei dati dei braccialetti)
@app.route('/api/v1/rfid/telemetry', methods=['GET'])
def get_rfid_data():
    token = request.headers.get('Authorization')
    if token != "Bearer JWT_ADMIN_VALIDO_12345":
        return jsonify({"error": "Unauthorized"}), 401
    
    # Questo è ciò che ruba l'attaccante dopo il Brute Force!
    mock_data = [
        {"bracelet_id": "RFID-8821", "owner": "John Doe", "cashless_balance": "150 Pearls", "location": "Main Stage"},
        {"bracelet_id": "RFID-9934", "owner": "Alice Smith", "cashless_balance": "45 Pearls", "location": "Food Court"}
    ]
    logging.info("DATA_ACCESS: Dati RFID esportati dalla dashboard.")
    return jsonify({"status": "LIVE_TELEMETRY", "data": mock_data}), 200

# 3. DEPLOY DEL MALWARE (Vulnerabile al Fake Update)
@app.route('/api/v1/app/deploy', methods=['POST'])
def deploy_update():
    token = request.headers.get('Authorization')
    if token != "Bearer JWT_ADMIN_VALIDO_12345":
        return jsonify({"error": "Unauthorized"}), 401
    
    file = request.files.get('update_file')
    if file:
        if SECURITY_MODE == "SECURE":
            content = file.read().decode('utf-8', errors='ignore')
            if not content.startswith("// SIGNED_BY_TML_CISO_2026"):
                logging.warning("SECURITY_ENFORCEMENT: Tentativo di upload di codice non firmato bloccato")
                return jsonify({"status": "error", "message": "Forbidden: Errore verifica firma digitale"}), 403
            file.seek(0)

        file.save(os.path.join('/tmp', file.filename))
        logging.info(f"UPDATE_PUSHED_SUCCESSFULLY: Fake Update '{file.filename}' inviato a 100.000 braccialetti.")
        return jsonify({"status": "CRITICAL_SUCCESS", "message": "Sistema Cashless compromesso. Update Pushato."}), 200
        return jsonify({"status": "CRITICAL_SUCCESS", "message": "Sistema Cashless compromesso. Update Pushato."}), 200
    return jsonify({"error": "Bad Request"}), 400

# 4. QUISHING / PHYSICAL SPOOFING (Caso 3)
from flask import render_template

@app.route('/promo', methods=['GET'])
def fake_sponsor_page():
    return render_template('sponsor_promo.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)