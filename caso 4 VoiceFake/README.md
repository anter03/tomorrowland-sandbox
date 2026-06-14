# 🔴 Panic Engine — SIP Spoofing & Deepfake Audio Injection POC

> **Progetto CSS (Cyber-Social Security)** — Caso di Studio "Festival AI-driven (Barletta)"  
> Validazione Unified Kill Chain in ambiente sandbox Docker

---

## ⚠️ Disclaimer

Questo Proof-of-Concept è sviluppato **esclusivamente per scopi accademici** nell'ambito del corso di Tecniche di Attacco e Difesa. L'infrastruttura opera in una **rete Docker isolata** (`10.5.0.0/24`) e non interagisce con sistemi esterni.

---

## Architettura

```
┌─────────────────────────────────────────────────────────────┐
│                    festival-net (10.5.0.0/24)                │
│                                                             │
│  ┌─────────────────┐   SIP INVITE    ┌──────────────────┐  │
│  │  host-attaccante │ ──────────────→ │   gateway-sip    │  │
│  │   10.5.0.99      │   (spoofed)     │   10.5.0.50      │  │
│  │   Python 3.10    │                 │   Asterisk PBX   │  │
│  │                  │   RTP stream    │                  │  │
│  │  attack.py       │ ──────────────→ │  [anonymous]     │  │
│  └─────────────────┘                 │   endpoint       │  │
│                                       │                  │  │
│                                       │   Dial(PJSIP/200)│  │
│                                       │        │         │  │
│                                       └────────┼─────────┘  │
│                                                │             │
│                                       ┌────────▼─────────┐  │
│                                       │ terminale-operat. │  │
│                                       │   10.5.0.200      │  │
│                                       │   Baresip          │  │
│                                       │   (auto-answer)   │  │
│                                       └──────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Nodi

| Container | IP | Ruolo | Tecnologia |
|---|---|---|---|
| `gateway-sip` | 10.5.0.50 | Centralino PBX vulnerabile | Asterisk + PJSIP |
| `terminale-operatore` | 10.5.0.200 | Radio PoC operatore ai varchi | Baresip (auto-answer) |
| `host-attaccante` | 10.5.0.99 | Threat Actor | Python 3.10 + socket |

---

## Vulnerabilità Simulate

| CWE | Nome | Dove | Effetto |
|-----|------|------|---------|
| **CWE-862** | Missing Authorization | `pjsip.conf` → `[anonymous]` | INVITE accettati senza autorizzazione |
| **CWE-287** | Improper Authentication | `pjsip.conf` → `[anonymous]` | Nessuna digest auth per chiamate esterne |

---

## Kill Chain Mapping

| Fase | Dominio | Azione | Script |
|------|---------|--------|--------|
| **Delivery** | Cyber | SIP INVITE spoofato con Caller-ID falsificato | `attack.py` Fase 1 |
| **C2 Establishment** | Cyber | Handshake SIP (100→180→200 OK→ACK) | `attack.py` Fase 2 |
| **Impact** | Cognitivo | RTP injection del deepfake audio | `attack.py` Fase 3 |

L'identità spoofata (`"Burgemeester Jeroen Baert" <sip:mayor@comune.boom.be>`) sfrutta il **bias di autorità** per innescare il tunneling cognitivo nell'operatore.

---

## Prerequisiti

- [Docker](https://www.docker.com/) ≥ 20.x
- [Docker Compose](https://docs.docker.com/compose/) ≥ 2.x
- GNU Make (opzionale, per i comandi abbreviati)

---

## Quick Start

### 1. Build e avvio dell'infrastruttura

```bash
# Con Make
make up

# Oppure direttamente
docker-compose up -d --build
```

### 2. Verifica che tutti i container siano attivi

```bash
make status
# oppure
docker-compose ps
```

### 3. Verifica registrazione SIP dell'operatore

```bash
make check-endpoints
# oppure
docker exec gateway-sip asterisk -rx "pjsip show endpoints"
```

Dovresti vedere l'endpoint `200` con stato `Avail`.

### 4. Genera il file audio di test (se non hai un deepfake WAV)

```bash
make generate-tone
# oppure
docker exec -it host-attaccante python /app/generate_tone.py
```

### 5. Monitora i log della vittima (in un terminale separato)

```bash
make logs
# oppure
docker logs -f terminale-operatore
```

### 6. Esegui l'attacco

```bash
make attack
# oppure
docker exec -it host-attaccante python /app/attack.py
```

**Output atteso sul terminale operatore:**
```
Incoming call from: Burgemeester Jeroen Baert <sip:mayor@comune.boom.be>
```

### 7. Verifica log di sicurezza (SIEM)

```bash
make siem
# oppure
cat logs/security.log
```

---

## Struttura del Progetto

```
centralino-tomorrowland/
├── docker-compose.yml          # Orchestrazione 3 container
├── Makefile                    # Comandi di orchestrazione
├── README.md                   # Questo file
├── gateway-sip/
│   ├── Dockerfile              # Alpine + Asterisk
│   ├── pjsip.conf              # Config SIP (VULNERABILE)
│   ├── extensions.conf         # Dialplan routing
│   ├── logger.conf             # Log per SIEM/Wazuh
│   ├── modules.conf            # Moduli Asterisk
│   └── rtp.conf                # Range porte RTP
├── terminale-operatore/
│   ├── Dockerfile              # Alpine + Baresip
│   ├── entrypoint.sh           # Wait-loop + avvio
│   └── baresip/
│       ├── config              # Auto-answer + G.711
│       └── accounts            # Registrazione SIP
├── host-attaccante/
│   ├── Dockerfile              # Python 3.10 + scapy
│   ├── attack.py               # Script di attacco 3 fasi
│   ├── generate_tone.py        # Generatore tono di test
│   ├── requirements.txt        # Dipendenze Python
│   └── payload/
│       └── deepfake_voice.wav  # File audio (da fornire)
└── logs/                       # Volume condiviso per SIEM
```

---

## Integrazione AGR (Blue Team)

### CTRL-C02: Isolamento Automatizzato API Gateway

I log di sicurezza di Asterisk sono esportati nel volume `./logs/` e sono leggibili da un'istanza SIEM esterna (Wazuh). Il file `security.log` contiene gli eventi di autenticazione e gli INVITE anomali.

Per collegare Wazuh, aggiungere al `docker-compose.yml` un container Wazuh agent che monta lo stesso volume `./logs/`.

---

## Cleanup

```bash
make down
# oppure
docker-compose down -v
```

---

## Riferimenti

- [RFC 3261 — SIP: Session Initiation Protocol](https://tools.ietf.org/html/rfc3261)
- [RFC 3550 — RTP: A Transport Protocol for Real-Time Applications](https://tools.ietf.org/html/rfc3550)
- [CWE-862: Missing Authorization](https://cwe.mitre.org/data/definitions/862.html)
- [CWE-287: Improper Authentication](https://cwe.mitre.org/data/definitions/287.html)
- [Asterisk PJSIP Configuration](https://docs.asterisk.org/Configuration/Channel-Drivers/SIP/Configuring-res_pjsip/)
