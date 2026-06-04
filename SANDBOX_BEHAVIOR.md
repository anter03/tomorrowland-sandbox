# Report di Comportamento e Test della Sandbox (Caso 7)

Questo documento descrive il funzionamento della Sandbox Docker multi-container (composta dal backend Flask e dal manager SIEM Wazuh) allineata alle specifiche del **Caso 7 (Festival AI-driven)** del MAIN PROJECT. 

La Sandbox dimostra empiricamente la differenza di comportamento tra uno scenario applicativo vulnerabile (soggetto ad attacco) e uno sicuro (mitigato) governati dalle variabili d'ambiente reali estratte dal file `.env`.

---

## 🛠️ Architettura e Logica Implementata

### 1. Controllo di Autenticazione (Backend Flask)
L'endpoint `POST /api/broadcast` gestisce la trasmissione di messaggi di emergenza nel festival. La logica applica i seguenti criteri:
- **Controllo Strutturale Mandatorio**: Qualsiasi richiesta deve includere l'header `X-Admin-Token` contenente una stringa di token crittografico JWT valida. Il server convalida la firma crittografica confrontandola con la chiave segreta di sistema (`SECRET_KEY` caricata da `.env`). Se il token è assente o la firma non coincide, la richiesta viene respinta immediatamente con **HTTP 401 (Unauthorized)**.
- **Bypass della Sicurezza Avanzata (Scenario Vulnerabile - `VULNERABILITY_ENABLED=false`)**:
  Il sistema ignora volutamente i controlli di scadenza del token (**CWE-613**) e la verifica dei privilegi/ruoli amministrativi (**CWE-862**). Un attacco eseguito con un token formalmente valido ma scaduto o con ruoli non autorizzati ha successo:
  - Ritorna **HTTP 200 (Successo)**.
  - Inserisce il messaggio nel database volatile dei broadcast.
  - Scrive nel log condiviso con il SIEM una stringa di allerta critica: `CRITICAL_API_BYPASS` in formato JSON strutturato.
- **Esecuzione Rigorosa (Scenario Sicuro - `VULNERABILITY_ENABLED=true`)**:
  Il backend esegue la validazione completa e blindata (**CTRL-C01**). Oltre alla struttura/firma del token, verifica tassativamente la scadenza temporale (`exp`) e l'autorizzazione del ruolo (`role: "admin"`). Se uno dei controlli fallisce, l'attacco viene respinto con **HTTP 401** e viene loggata la stringa `UNAUTHORIZED_ACCESS` in formato JSON.

### 2. Struttura Dati Volatile e API di Consultazione
- I messaggi broadcast inviati con successo vengono memorizzati all'interno di una lista temporanea in memoria (`broadcast_messages`) centralizzata nel processo Flask.
- È esposto l'endpoint pubblico `GET /api/messages` che restituisce l'elenco dei messaggi inviati in formato JSON (senza richiedere autenticazione crittografica).

### 3. Ripristino del Polling e Sincronizzazione (Front-end)
L'interfaccia utente in [index.html](file:///c:/Uni%20-%20proegtto%20TAD/tomorrowland-sandbox/backend/app/templates/index.html) è stata allineata per visualizzare la propagazione dell'attacco:
- Esegue in background un **loop di polling sincrono temporizzato a 2 secondi** (2000 millisecondi) verso l'endpoint di consultazione `GET /api/messages`.
- All'arrivo di nuovi messaggi, il client rimuove l'interfaccia standard dell'app e mostra dinamicamente a schermo intero il banner grafico di emergenza rosso (`#panic-banner`) visualizzando il messaggio iniettato in tempo reale.

### 4. Integrazione, Rilevamento e Persistenza SIEM Wazuh
Wazuh monitora in tempo reale il log `/var/log/tomorrowland_festival/festival_app.log` tramite il modulo di log-collection JSON configurato in `ossec.conf`.
- Le regole in [local_rules.xml](file:///c:/Uni%20-%20proegtto%20TAD/tomorrowland-sandbox/wazuh_config/local_rules.xml) decodificano il log nativamente come JSON ed ereditano dalla regola nativa `86600`:
  - **Regola 100011 (Livello 5)**: Rileva `UNAUTHORIZED_ACCESS` (tentativo di attacco sventato - MITRE T1190).
  - **Regola 100012 (Livello 12)**: Rileva `CRITICAL_API_BYPASS` (incidente di sicurezza grave - MITRE T1078/T1498).
- **Persistenza dei Log**: L'intera cartella `/var/ossec/logs` del container Wazuh è mappata sulla directory host `./logs/wazuh_logs/`. Tutti gli alert generati da Wazuh sono salvati in modo permanente sull'host in `logs/wazuh_logs/alerts/alerts.json` e rimangono persistiti anche dopo lo spegnimento dei container (`docker-compose down`).

---

## 🧪 Protocollo di Verifica Sperimentale

Per testare le risposte della Sandbox, sono stati forniti i seguenti script client Python:
- [send_valid_admin.py](file:///c:/Uni%20-%20proegtto%20TAD/tomorrowland-sandbox/send_valid_admin.py): Genera ed invia un token amministrativo valido.
- [send_invalid_token.py](file:///c:/Uni%20-%20proegtto%20TAD/tomorrowland-sandbox/send_invalid_token.py): Genera ed invia un token non valido (scaduto).

### Matrice di Comportamento nei Test

| Scenario di Test | Stato .env (`VULNERABILITY_ENABLED`) | Token Utilizzato | Esito API Broadcast | Impatto Front-end | Alert Wazuh (`alerts.json`) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Anonimo** | *Qualsiasi* | Nessuno / Vuoto | **401 Unauthorized** | Nessuno | `UNAUTHORIZED_ACCESS` (Livello 5) |
| **2. Vulnerabile** | `false` | Scaduto / Non-Admin | **200 OK** | **Evacuazione immediata visualizzata** (entro 2s) | `CRITICAL_API_BYPASS` (Livello 12 - Incidente) |
| **3. Sicuro (Mitigato)** | `true` | Scaduto / Non-Admin | **401 Unauthorized** | Nessuno (UI regolare attiva) | `UNAUTHORIZED_ACCESS` (Livello 5) |
| **4. Amministratore** | `true` | Valido Admin | **200 OK** | **Evacuazione visualizzata** (entro 2s) | `BROADCAST_SUCCESS` (Livello 3 - Informativo) |

---

## 📁 Posizione dei File Chiave del Laboratorio

- **Backend logic**: [server.py](file:///c:/Uni%20-%20proegtto%20TAD/tomorrowland-sandbox/backend/app/server.py)
- **Frontend interface**: [index.html](file:///c:/Uni%20-%20proegtto%20TAD/tomorrowland-sandbox/backend/app/templates/index.html)
- **Docker configuration**: [docker-compose.yml](file:///c:/Uni%20-%20proegtto%20TAD/tomorrowland-sandbox/docker-compose.yml)
- **SIEM Rules**: [local_rules.xml](file:///c:/Uni%20-%20proegtto%20TAD/tomorrowland-sandbox/wazuh_config/local_rules.xml)
- **SIEM configuration**: [ossec.conf](file:///c:/Uni%20-%20proegtto%20TAD/tomorrowland-sandbox/wazuh_config/ossec.conf)
- **Persistent Host Alerts log**: `logs/wazuh_logs/alerts/alerts.json`
