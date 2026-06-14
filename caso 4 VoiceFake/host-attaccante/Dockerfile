# ============================================================
#  Host Attaccante — Ambiente Offensivo Python
# ============================================================
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tcpdump \
    iputils-ping \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia script e payload
COPY attack.py .
COPY generate_tone.py .
COPY payload/ ./payload/

# Container resta in attesa — l'attacco è eseguito manualmente
CMD ["sleep", "infinity"]
