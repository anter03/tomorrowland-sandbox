# ============================================================
#  Terminale Operatore — Client SIP Python (Vittima)
#  Simula la radio PoC del personale ai varchi del festival
#
#  Usa un client SIP minimalista Python perché né baresip
#  né pjsua sono disponibili nei repo Alpine come binari.
# ============================================================
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY sip_client.py /app/sip_client.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5060/udp

ENTRYPOINT ["/entrypoint.sh"]
