#!/bin/bash
# ============================================================
#  Entrypoint — Terminale Operatore (SIP Client Python)
#  Attende che Asterisk sia raggiungibile, poi avvia il client
# ============================================================

GATEWAY_IP="10.5.0.50"
GATEWAY_PORT="5060"

echo "[*] Attendendo che il gateway SIP ($GATEWAY_IP:$GATEWAY_PORT) sia raggiungibile..."

MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    echo "test" | nc -u -w 1 "$GATEWAY_IP" "$GATEWAY_PORT" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "[+] Gateway SIP raggiungibile!"
        break
    fi
    RETRY=$((RETRY + 1))
    echo "[*] Tentativo $RETRY/$MAX_RETRIES — in attesa..."
    sleep 2
done

sleep 5

echo "[*] Avvio SIP Client — registrazione come endpoint 200..."
echo "[*] Auto-answer ABILITATO"
echo ""

exec python3 -u /app/sip_client.py
