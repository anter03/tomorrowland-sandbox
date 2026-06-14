# ============================================================
#  Panic Engine POC — Makefile di Orchestrazione
# ============================================================

.PHONY: up down logs attack status siem clean

## Avvia l'intera infrastruttura (build + deploy)
up:
	docker-compose up -d --build

## Ferma e rimuovi tutti i container e volumi
down:
	docker-compose down -v

## Mostra lo stato dei container
status:
	docker-compose ps

## Segui i log del terminale operatore (vittima)
## Cercare: "Incoming call from: Burgemeester Jeroen Baert"
logs:
	docker logs -f terminale-operatore

## Segui i log di Asterisk (gateway)
logs-gw:
	docker logs -f gateway-sip

## Esegui l'attacco dal container attaccante
attack:
	docker exec -it host-attaccante python /app/attack.py

## Genera il file audio di test (tono 440 Hz, 5 secondi)
generate-tone:
	docker exec -it host-attaccante python /app/generate_tone.py

## Mostra i log di sicurezza (SIEM / Wazuh)
siem:
	@if exist logs\security.log ( type logs\security.log ) else ( echo "Nessun log di sicurezza trovato. Avviare prima l'infrastruttura con 'make up'." )

## Verifica registrazione endpoint su Asterisk
check-endpoints:
	docker exec gateway-sip asterisk -rx "pjsip show endpoints"

## Pulisci tutto (container, immagini, log)
clean: down
	docker-compose rm -f
	del /Q logs\*.log 2>nul || true
