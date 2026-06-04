# Report dei Risultati dei Test della Sandbox

Questo report documenta le verifiche sperimentali condotte sulla Sandbox Docker multi-container dopo la pulizia completa dei log e degli alert. 

Tutti i test sono stati eseguiti inviando richieste verso l'endpoint `/api/broadcast` del backend. Gli alert generati sono stati letti direttamente dal file persistente dell'host `logs/wazuh_logs/alerts/alerts.json`.

---

## 📋 Riepilogo dei Test Condotti

### Test 1: Chiamata Anonima (Senza Header Token)
- **Stato Interruttore**: Scenario Vulnerabile (`VULNERABILITY_ENABLED=false`)
- **Comando Eseguito**:
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:5000/api/broadcast" -Method Post -ContentType "application/json" -Body '{"message": "ATTENZIONE: Messaggio di test anonimo."}'
  ```
- **Esito API (Risposta Server)**:
  `HTTP 401 Unauthorized`
  ```json
  {
    "error": "Unauthorized - Missing Token"
  }
  ```
- **Log Applicativo (`logs/festival_app.log`)**:
  ```json
  {"timestamp": "2026-06-04T16:21:24.716536Z", "level": "WARNING", "EVENT_TYPE": "UNAUTHORIZED_ACCESS", "ip": "172.19.0.1", "endpoint": "/api/broadcast", "error": "Missing token header"}
  ```
- **Alert Generato da Wazuh (`logs/wazuh_logs/alerts/alerts.json`)**:
  ```json
  {
    "timestamp": "2026-06-04T16:21:25.004+0000",
    "rule": {
      "level": 5,
      "description": "Festival App: Tentativo di accesso non autorizzato all'API di Broadcast",
      "id": "100011",
      "mitre": {
        "id": ["T1190"],
        "tactic": ["Initial Access"],
        "technique": ["Exploit Public-Facing Application"]
      },
      "firedtimes": 1,
      "mail": false,
      "groups": ["festival_app_security"]
    },
    "agent": { "id": "000", "name": "9fd017dbd0f0" },
    "manager": { "name": "9fd017dbd0f0" },
    "id": "1780590085.810664",
    "full_log": "{\"timestamp\":\"2026-06-04T16:21:24.716536Z\",\"level\":\"WARNING\",\"EVENT_TYPE\":\"UNAUTHORIZED_ACCESS\",\"ip\":\"172.19.0.1\",\"endpoint\":\"/api/broadcast\",\"error\":\"Missing token header\"}",
    "decoder": { "name": "json" },
    "data": {
      "timestamp": "2026-06-04T16:21:24.716536Z",
      "level": "WARNING",
      "EVENT_TYPE": "UNAUTHORIZED_ACCESS",
      "ip": "172.19.0.1",
      "endpoint": "/api/broadcast",
      "error": "Missing token header"
    },
    "location": "/var/log/tomorrowland_festival/festival_app.log"
  }
  ```

---

### Test 2: Vettore d'Attacco in Scenario Vulnerabile (Token Scaduto)
- **Stato Interruttore**: Scenario Vulnerabile (`VULNERABILITY_ENABLED=false`)
- **Comando Eseguito**:
  ```powershell
  python send_invalid_token.py
  ```
- **Esito API (Risposta Server)**:
  `HTTP 200 OK`
  ```json
  {
    "message": "Broadcast inviato (Scenario Vulnerabile - Scadenza e Ruoli non verificati)",
    "status": "success"
  }
  ```
- **Impatto sul Front-end**:
  L'interfaccia client (in `index.html`) ha intercettato il messaggio entro 2 secondi dal polling, nascondendo l'app standard ed attivando il banner rosso di allerta evacuazione con il testo: `"ATTENZIONE: Evacuazione immediata stage!"`.
- **Log Applicativo (`logs/festival_app.log`)**:
  ```json
  {"timestamp": "2026-06-04T16:21:33.296385Z", "level": "WARNING", "EVENT_TYPE": "CRITICAL_API_BYPASS", "ip": "172.19.0.1", "msg": "ATTENZIONE: Evacuazione immediata stage!", "status": "Exploited via Expired/Low-Privilege Token"}
  ```
- **Alert Generato da Wazuh (`logs/wazuh_logs/alerts/alerts.json`)**:
  ```json
  {
    "timestamp": "2026-06-04T16:21:35.016+0000",
    "rule": {
      "level": 12,
      "description": "Festival App INCIDENT: Bypass dell'autenticazione sfruttato su /api/broadcast. Rischio di manipolazione Dominio Informativo imminente.",
      "id": "100012",
      "mitre": {
        "id": ["T1078", "T1498"],
        "tactic": ["Defense Evasion", "Persistence", "Privilege Escalation", "Initial Access", "Impact"],
        "technique": ["Valid Accounts", "Network Denial of Service"]
      },
      "firedtimes": 1,
      "mail": true,
      "groups": ["festival_app_security", "authentication_bypass", " pci_dss_10.2.4"]
    },
    "agent": { "id": "000", "name": "9fd017dbd0f0" },
    "manager": { "name": "9fd017dbd0f0" },
    "id": "1780590095.812502",
    "full_log": "{\"timestamp\":\"2026-06-04T16:21:33.296385Z\",\"level\":\"WARNING\",\"EVENT_TYPE\":\"CRITICAL_API_BYPASS\",\"ip\":\"172.19.0.1\",\"msg\":\"ATTENZIONE: Evacuazione immediata stage!\",\"status\":\"Exploited via Expired/Low-Privilege Token\"}",
    "decoder": { "name": "json" },
    "data": {
      "status": "Exploited via Expired/Low-Privilege Token",
      "timestamp": "2026-06-04T16:21:33.296385Z",
      "level": "WARNING",
      "EVENT_TYPE": "CRITICAL_API_BYPASS",
      "ip": "172.19.0.1",
      "msg": "ATTENZIONE: Evacuazione immediata stage!"
    },
    "location": "/var/log/tomorrowland_festival/festival_app.log"
  }
  ```

---

### Test 3: Attacco Bloccato in Scenario Sicuro (Token Scaduto)
- **Stato Interruttore**: Scenario Sicuro (`VULNERABILITY_ENABLED=true`)
- **Comando Eseguito**:
  ```powershell
  python send_invalid_token.py
  ```
- **Esito API (Risposta Server)**:
  `HTTP 401 Unauthorized`
  ```json
  {
    "error": "Unauthorized - Token Expired"
  }
  ```
- **Impatto sul Front-end**:
  Nessuno. L'interfaccia client ha continuato a mostrare la visualizzazione standard Tomorrowland App (nessun allarme evacuazione inserito).
- **Log Applicativo (`logs/festival_app.log`)**:
  ```json
  {"timestamp": "2026-06-04T16:21:54.011639Z", "level": "WARNING", "EVENT_TYPE": "UNAUTHORIZED_ACCESS", "ip": "172.19.0.1", "endpoint": "/api/broadcast", "error": "Token signature has expired"}
  ```
- **Alert Generato da Wazuh (`logs/wazuh_logs/alerts/alerts.json`)**:
  ```json
  {
    "timestamp": "2026-06-04T16:21:55.053+0000",
    "rule": {
      "level": 5,
      "description": "Festival App: Tentativo di accesso non autorizzato all'API di Broadcast",
      "id": "100011",
      "mitre": {
        "id": ["T1190"],
        "tactic": ["Initial Access"],
        "technique": ["Exploit Public-Facing Application"]
      },
      "firedtimes": 2,
      "mail": false,
      "groups": ["festival_app_security"]
    },
    "agent": { "id": "000", "name": "9fd017dbd0f0" },
    "manager": { "name": "9fd017dbd0f0" },
    "id": "1780590115.814502",
    "full_log": "{\"timestamp\":\"2026-06-04T16:21:54.011639Z\",\"level\":\"WARNING\",\"EVENT_TYPE\":\"UNAUTHORIZED_ACCESS\",\"ip\":\"172.19.0.1\",\"endpoint\":\"/api/broadcast\",\"error\":\"Token signature has expired\"}",
    "decoder": { "name": "json" },
    "data": {
      "timestamp": "2026-06-04T16:21:54.011639Z",
      "level": "WARNING",
      "EVENT_TYPE": "UNAUTHORIZED_ACCESS",
      "ip": "172.19.0.1",
      "endpoint": "/api/broadcast",
      "error": "Token signature has expired"
    },
    "location": "/var/log/tomorrowland_festival/festival_app.log"
  }
  ```

---

### Test 4: Chiamata Regolare in Scenario Sicuro (Token Admin Valido)
- **Stato Interruttore**: Scenario Sicuro (`VULNERABILITY_ENABLED=true`)
- **Comando Eseguito**:
  ```powershell
  python send_valid_admin.py
  ```
- **Esito API (Risposta Server)**:
  `HTTP 200 OK`
  ```json
  {
    "message": "Broadcast inviato regolarmente dall'amministratore verificato",
    "status": "success"
  }
  ```
- **Log Applicativo (`logs/festival_app.log`)**:
  ```json
  {"timestamp": "2026-06-04T16:22:02.166209Z", "level": "INFO", "EVENT_TYPE": "BROADCAST_SUCCESS", "ip": "172.19.0.1", "msg": "MESSAGGIO AUTORIZZATO: Tutto sotto controllo."}
  ```
- **Alert Generato da Wazuh (`logs/wazuh_logs/alerts/alerts.json`)**:
  ```json
  {
    "timestamp": "2026-06-04T16:22:03.063+0000",
    "rule": {
      "level": 3,
      "description": "Festival App: Evento generico registrato",
      "id": "100010",
      "firedtimes": 1,
      "mail": false,
      "groups": ["festival_app_security"]
    },
    "agent": { "id": "000", "name": "9fd017dbd0f0" },
    "manager": { "name": "9fd017dbd0f0" },
    "id": "1780590123.815081",
    "full_log": "{\"timestamp\":\"2026-06-04T16:22:02.166209Z\",\"level\":\"INFO\",\"EVENT_TYPE\":\"BROADCAST_SUCCESS\",\"ip\":\"172.19.0.1\",\"msg\":\"MESSAGGIO AUTORIZZATO: Tutto sotto controllo.\"}",
    "decoder": { "name": "json" },
    "data": {
      "timestamp": "2026-06-04T16:22:02.166209Z",
      "level": "INFO",
      "EVENT_TYPE": "BROADCAST_SUCCESS",
      "ip": "172.19.0.1",
      "msg": "MESSAGGIO AUTORIZZATO: Tutto sotto controllo."
    },
    "location": "/var/log/tomorrowland_festival/festival_app.log"
  }
  ```

---

## 💾 Persistenza dei Log sull'Host
Il file degli alert `alerts.json` (che include i dettagli sopra riportati per ogni evento di sicurezza) è memorizzato in modo persistente nella cartella `./logs/wazuh_logs/alerts/` sul disco dell'host. Questo archivio rimane integro e consultabile anche quando tutti i container Docker vengono distrutti.
