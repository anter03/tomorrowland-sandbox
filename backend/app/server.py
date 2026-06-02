from flask import Flask, request, jsonify, send_from_directory
import jwt
import logging
import os

app = Flask(__name__)

# Assicura che la cartella logs esista all'interno del container
os.makedirs('logs', exist_ok=True)

# Configurazione del logger applicativo
logging.basicConfig(filename='logs/tomorrowland_api.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - IP:%(client_ip)s - MSG:%(message)s')

SECRET_KEY = "chiave_segreta_del_festival"
current_alert = None  # Stato globale che simula il sistema push in-app

@app.route('/')
def index():
    # Rende disponibile l'interfaccia dell'App del partecipante
    return send_from_directory('.', 'index.html')

@app.route('/api/v1/alert', methods=['GET'])
def get_alert():
    global current_alert
    return jsonify({"alert": current_alert})

@app.route('/api/v1/broadcast/alert', methods=['POST'])
def send_alert():
    global current_alert
    auth_header = request.headers.get('Authorization')
    client_ip = request.remote_addr

    if not auth_header or not auth_header.startswith('Bearer '):
        logging.info("Tentativo di accesso non autenticato", extra={'client_ip': client_ip})
        return jsonify({"error": "Non autorizzato"}), 401

    token = auth_header.split(" ")[1]

    try:
        # VULNERABILITÀ CRITICA:
        # 1. (CWE-613) La verifica della scadenza del token è disattivata (verify_exp=False)
        # 2. (CWE-862) Mancanza di controllo dei ruoli (RBAC): chiunque abbia un token valido può inviare l'alert
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})

        data = request.json or {}
        alert_msg = data.get("message", "Evacuazione Imminente!")
        current_alert = alert_msg  # Attiva l'allarme per tutti i frontend connessi

        logging.info(f"ALERT INVIATO CON SUCCESSO dal partecipante {payload.get('user', 'unknown')}: {alert_msg}", extra={'client_ip': client_ip})
        return jsonify({"status": "Broadcast inviato alla folla", "message": alert_msg}), 200

    except jwt.InvalidTokenError:
        logging.info("Tentativo di attacco con Token non valido (Firma fallita)", extra={'client_ip': client_ip})
        return jsonify({"error": "Token non valido"}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)