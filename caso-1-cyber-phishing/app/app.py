import logging
import os
from flask import Flask, request, jsonify

app = Flask(__name__)
os.makedirs('/var/log/tomorrowland', exist_ok=True)
logging.basicConfig(filename='/var/log/tomorrowland/cyber_dashboard.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

STAFF_DB = {"m.rossi@tomorrowland.com": "cashless2026"}

# 1. AUTENTICAZIONE (Vulnerabile al Brute Force)
@app.route('/api/v1/staff/auth', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    
    if username in STAFF_DB and STAFF_DB[username] == password:
        logging.info(f"AUTH_SUCCESS: {username} è entrato nella Dashboard Crowd AI.")
        return jsonify({"token": "JWT_ADMIN_VALIDO_12345", "role": "Crowd_Manager"}), 200
    else:
        logging.warning(f"AUTH_FAIL: Tentativo di accesso fallito per {username} dall'IP {request.remote_addr}")
        return jsonify({"status": "error", "message": "Credenziali errate"}), 401

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
        file.save(os.path.join('/tmp', file.filename))
        logging.info(f"UPDATE_PUSHED_SUCCESSFULLY: Fake Update '{file.filename}' inviato a 100.000 braccialetti.")
        return jsonify({"status": "CRITICAL_SUCCESS", "message": "Sistema Cashless compromesso. Update Pushato."}), 200
    return jsonify({"error": "Bad Request"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)