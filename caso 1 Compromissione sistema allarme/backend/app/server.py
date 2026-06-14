import os
import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template
import jwt

app = Flask(__name__)

# Log condiviso con Wazuh
LOG_PATH = "/var/log/tomorrowland_festival/festival_app.log"
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format='%(message)s')

# Database temporaneo in memoria per i messaggi del broadcast
broadcast_messages = []

# Funzione helper per il logging in formato JSON (compatibile con Wazuh json decoder)
def log_event(event_type, level="INFO", **kwargs):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "EVENT_TYPE": event_type,
        **kwargs
    }
    msg = json.dumps(log_entry)
    if level == "ERROR":
        logging.error(msg)
    elif level == "WARNING":
        logging.warning(msg)
    else:
        logging.info(msg)

@app.route('/')
def index():
    return render_template('index.html')

# ENDPOINT PER IL POLLING DEL FRONT-END (Ogni 2 secondi)
@app.route('/api/messages', methods=['GET'])
def get_messages():
    return jsonify({"messages": broadcast_messages}), 200

# ENDPOINT CRITICO DI BROADCAST
@app.route('/api/broadcast', methods=['POST'])
def emergency_broadcast():
    token = request.headers.get('X-Admin-Token')
    client_ip = request.remote_addr
    payload_msg = request.json.get('message', '') if request.json else ''

    # 1. IL TOKEN DEVE ESSERE SEMPRE PRESENTE (Controllo Base)
    if not token:
        log_event(
            event_type="UNAUTHORIZED_ACCESS",
            level="WARNING",
            ip=client_ip,
            endpoint="/api/broadcast",
            error="Missing token header"
        )
        return jsonify({"error": "Unauthorized - Missing Token"}), 401

    secret_key = os.getenv("SECRET_KEY", "chiave_segreta_del_festival")
    is_secure = os.getenv("VULNERABILITY_ENABLED", "true").lower() == "true"

    try:
        if not is_secure:
            # 2. SCENARIO VULNERABILE (VULNERABILITY_ENABLED=false)
            # VIOLAZIONE: Il token esiste ed è strutturalmente valido (firma corretta),
            # ma non controlliamo la scadenza (CWE-613) né i ruoli (CWE-862)
            # L'attacco ha successo sfruttando un token scaduto o di basso livello.
            decoded_token = jwt.decode(token, secret_key, algorithms=['HS256'], options={"verify_exp": False})
            
            # L'attacco ha successo! Inseriamo il messaggio nella lista dei broadcast.
            broadcast_messages.append(payload_msg)
            
            # Scriviamo nel log l'allerta critica per Wazuh: CRITICAL_API_BYPASS
            log_event(
                event_type="CRITICAL_API_BYPASS",
                level="WARNING",
                ip=client_ip,
                msg=payload_msg,
                status="Exploited via Expired/Low-Privilege Token"
            )
            return jsonify({
                "status": "success",
                "message": "Broadcast inviato (Scenario Vulnerabile - Scadenza e Ruoli non verificati)"
            }), 200
        else:
            # 3. SCENARIO SICURO (VULNERABILITY_ENABLED=true)
            # Controllo rigoroso:
            # - Verifica della firma nativa (confronto con la chiave segreta)
            # - Verifica temporale (scadenza)
            # - Autorizzazione del ruolo (deve essere 'admin')
            decoded_token = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            if decoded_token.get('role') != 'admin':
                log_event(
                    event_type="UNAUTHORIZED_ACCESS",
                    level="WARNING",
                    ip=client_ip,
                    endpoint="/api/broadcast",
                    error="Forbidden - Insufficient privileges"
                )
                return jsonify({"error": "Unauthorized - Insufficient privileges"}), 401

            # Flusso sicuro ed autorizzato al 100%
            broadcast_messages.append(payload_msg)
            log_event(
                event_type="BROADCAST_SUCCESS",
                level="INFO",
                ip=client_ip,
                msg=payload_msg
            )
            return jsonify({
                "status": "success",
                "message": "Broadcast inviato regolarmente dall'amministratore verificato"
            }), 200

    except jwt.ExpiredSignatureError as e:
        log_event(
            event_type="UNAUTHORIZED_ACCESS",
            level="WARNING",
            ip=client_ip,
            endpoint="/api/broadcast",
            error="Token signature has expired"
        )
        return jsonify({"error": "Unauthorized - Token Expired"}), 401
    except jwt.InvalidTokenError as e:
        log_event(
            event_type="UNAUTHORIZED_ACCESS",
            level="WARNING",
            ip=client_ip,
            endpoint="/api/broadcast",
            error=f"Invalid token signature or structure: {str(e)}"
        )
        return jsonify({"error": "Unauthorized - Invalid Token Structure"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)