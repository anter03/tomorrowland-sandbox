#!/usr/bin/env python3
"""
============================================================
 Client SIP Minimalista — Terminale Operatore (Vittima)
 
 Implementa un endpoint SIP che:
   1. Si registra su Asterisk come interno 200
   2. Accetta automaticamente le chiamate in ingresso (auto-answer)
   3. Logga il Caller-ID di ogni chiamata ricevuta
 
 Questo client simula il comportamento di una radio PoC
 (Push-to-Talk over Cellular) del personale ai varchi,
 che apre il canale bidirezionale senza interazione umana.
============================================================
"""

import socket
import hashlib
import random
import string
import time
import sys
import re

# ─── CONFIGURAZIONE ──────────────────────────────────────────

LOCAL_IP     = "10.5.0.200"
LOCAL_PORT   = 5060
GATEWAY_IP   = "10.5.0.50"
GATEWAY_PORT = 5060

SIP_USER     = "200"
SIP_PASS     = "operatore123"
SIP_DOMAIN   = GATEWAY_IP

# ─── UTILITÀ ─────────────────────────────────────────────────

def random_tag(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def random_branch():
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    return f"z9hG4bK{suffix}"

def random_callid():
    return f"{random.randint(100000, 999999)}@{LOCAL_IP}"

def compute_digest(username, realm, password, method, uri, nonce):
    """Calcola la risposta digest auth (RFC 2617)."""
    ha1 = hashlib.md5(f"{username}:{realm}:{password}".encode()).hexdigest()
    ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()
    response = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()
    return response


# ─── SIP REGISTER ────────────────────────────────────────────

def register(sock, auth_response=None, nonce=None, realm=None):
    """Invia REGISTER al gateway SIP."""
    branch = random_branch()
    tag = random_tag()
    callid = random_callid()

    register_msg = (
        f"REGISTER sip:{SIP_DOMAIN} SIP/2.0\r\n"
        f"Via: SIP/2.0/UDP {LOCAL_IP}:{LOCAL_PORT};branch={branch};rport\r\n"
        f"From: <sip:{SIP_USER}@{SIP_DOMAIN}>;tag={tag}\r\n"
        f"To: <sip:{SIP_USER}@{SIP_DOMAIN}>\r\n"
        f"Call-ID: {callid}\r\n"
        f"CSeq: 1 REGISTER\r\n"
        f"Contact: <sip:{SIP_USER}@{LOCAL_IP}:{LOCAL_PORT}>\r\n"
        f"Expires: 3600\r\n"
        f"Max-Forwards: 70\r\n"
        f"User-Agent: PoC-Radio-Terminal/1.0\r\n"
    )

    if auth_response and nonce and realm:
        uri = f"sip:{SIP_DOMAIN}"
        register_msg += (
            f'Authorization: Digest username="{SIP_USER}", '
            f'realm="{realm}", '
            f'nonce="{nonce}", '
            f'uri="{uri}", '
            f'response="{auth_response}"\r\n'
        )

    register_msg += f"Content-Length: 0\r\n\r\n"

    sock.sendto(register_msg.encode(), (GATEWAY_IP, GATEWAY_PORT))
    print(f"[>] REGISTER inviato a {GATEWAY_IP}:{GATEWAY_PORT}")


def handle_register_response(sock):
    """Gestisce la risposta al REGISTER (401 → digest auth → 200 OK)."""
    sock.settimeout(10)

    try:
        data, addr = sock.recvfrom(4096)
        response = data.decode('utf-8', errors='replace')
        first_line = response.split('\r\n')[0]
        print(f"[<] {first_line}")

        # 401 Unauthorized — serve digest auth
        if 'SIP/2.0 401' in first_line:
            # Estrai realm e nonce dall'header WWW-Authenticate
            nonce = realm = None
            for line in response.split('\r\n'):
                if line.lower().startswith('www-authenticate'):
                    nonce_match = re.search(r'nonce="([^"]+)"', line)
                    realm_match = re.search(r'realm="([^"]+)"', line)
                    if nonce_match:
                        nonce = nonce_match.group(1)
                    if realm_match:
                        realm = realm_match.group(1)

            if nonce and realm:
                print(f"    → Auth richiesta (realm={realm})")
                uri = f"sip:{SIP_DOMAIN}"
                digest = compute_digest(SIP_USER, realm, SIP_PASS, "REGISTER", uri, nonce)
                register(sock, auth_response=digest, nonce=nonce, realm=realm)

                # Attendi risposta alla registrazione autenticata
                data2, addr2 = sock.recvfrom(4096)
                response2 = data2.decode('utf-8', errors='replace')
                first_line2 = response2.split('\r\n')[0]
                print(f"[<] {first_line2}")

                if 'SIP/2.0 200' in first_line2:
                    print("[+] ✅ REGISTRAZIONE RIUSCITA come endpoint 200")
                    return True
                else:
                    print(f"[!] Registrazione fallita: {first_line2}")
                    return False
            else:
                print("[!] Impossibile estrarre nonce/realm dal 401")
                return False

        elif 'SIP/2.0 200' in first_line:
            print("[+] ✅ REGISTRAZIONE RIUSCITA come endpoint 200")
            return True

        else:
            print(f"[!] Risposta inattesa: {first_line}")
            return False

    except socket.timeout:
        print("[!] Timeout durante la registrazione")
        return False


# ─── SIP CALL HANDLER (AUTO-ANSWER) ─────────────────────────

def handle_incoming_invite(sock, data, addr):
    """
    Gestisce un INVITE in ingresso con auto-answer.
    Logga il Caller-ID e risponde con 200 OK.
    """
    request = data.decode('utf-8', errors='replace')

    # Estrai Caller-ID
    caller_name = "Unknown"
    caller_uri = "unknown"
    for line in request.split('\r\n'):
        if line.lower().startswith('from:'):
            # Parse display name
            name_match = re.search(r'"([^"]+)"', line)
            if name_match:
                caller_name = name_match.group(1)
            # Parse URI
            uri_match = re.search(r'<([^>]+)>', line)
            if uri_match:
                caller_uri = uri_match.group(1)
            break

    print(f"\n{'='*60}")
    print(f"  📞 INCOMING CALL")
    print(f"  Incoming call from: {caller_name}")
    print(f"  URI: {caller_uri}")
    print(f"{'='*60}")

    # Estrai header necessari per la risposta
    via = ""
    from_h = ""
    to_h = ""
    callid_h = ""
    cseq_h = ""
    contact_h = ""

    for line in request.split('\r\n'):
        if line.lower().startswith('via:') and not via:
            via = line
        elif line.lower().startswith('from:'):
            from_h = line
        elif line.lower().startswith('to:'):
            to_h = line
        elif line.lower().startswith('call-id:'):
            callid_h = line
        elif line.lower().startswith('cseq:'):
            cseq_h = line
        elif line.lower().startswith('contact:'):
            contact_h = line

    # Aggiungi tag al To se non presente
    if ';tag=' not in to_h:
        to_h += f";tag={random_tag()}"

    # ── Invia 100 Trying ──
    trying = (
        f"SIP/2.0 100 Trying\r\n"
        f"{via}\r\n"
        f"{from_h}\r\n"
        f"{to_h}\r\n"
        f"{callid_h}\r\n"
        f"{cseq_h}\r\n"
        f"Content-Length: 0\r\n"
        f"\r\n"
    )
    sock.sendto(trying.encode(), addr)
    print("[>] 100 Trying")

    # ── Invia 180 Ringing ──
    ringing = (
        f"SIP/2.0 180 Ringing\r\n"
        f"{via}\r\n"
        f"{from_h}\r\n"
        f"{to_h}\r\n"
        f"{callid_h}\r\n"
        f"{cseq_h}\r\n"
        f"Content-Length: 0\r\n"
        f"\r\n"
    )
    sock.sendto(ringing.encode(), addr)
    print("[>] 180 Ringing")

    # Breve pausa per simulare lo squillo
    time.sleep(0.5)

    # ── Invia 200 OK con SDP (auto-answer) ──
    rtp_port = 20000 + random.randint(0, 100)
    sdp_body = (
        f"v=0\r\n"
        f"o=operator 987654 987654 IN IP4 {LOCAL_IP}\r\n"
        f"s=PoC Radio Terminal\r\n"
        f"c=IN IP4 {LOCAL_IP}\r\n"
        f"t=0 0\r\n"
        f"m=audio {rtp_port} RTP/AVP 0\r\n"
        f"a=rtpmap:0 PCMU/8000\r\n"
    )

    ok_200 = (
        f"SIP/2.0 200 OK\r\n"
        f"{via}\r\n"
        f"{from_h}\r\n"
        f"{to_h}\r\n"
        f"{callid_h}\r\n"
        f"{cseq_h}\r\n"
        f"Contact: <sip:{SIP_USER}@{LOCAL_IP}:{LOCAL_PORT}>\r\n"
        f"Content-Type: application/sdp\r\n"
        f"Content-Length: {len(sdp_body)}\r\n"
        f"\r\n"
        f"{sdp_body}"
    )
    sock.sendto(ok_200.encode(), addr)
    print(f"[>] 200 OK (auto-answer) — RTP port {rtp_port}")
    print(f"[*] 🎙️  Canale audio aperto — ascoltando deepfake audio...")

    return True


# ─── MAIN LOOP ───────────────────────────────────────────────

def main():
    print("="*60)
    print("  TERMINALE OPERATORE — Radio PoC Varchi Festival")
    print("  SIP Client con Auto-Answer")
    print("="*60)
    print()

    # Crea socket SIP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LOCAL_IP, LOCAL_PORT))
    print(f"[*] Socket SIP in ascolto su {LOCAL_IP}:{LOCAL_PORT}")

    # Registrazione
    print(f"\n[*] Registrazione su {GATEWAY_IP}:{GATEWAY_PORT} come '{SIP_USER}'...")
    register(sock)
    registered = handle_register_response(sock)

    if not registered:
        print("[!] Registrazione fallita — riprovo tra 5 secondi...")
        time.sleep(5)
        register(sock)
        registered = handle_register_response(sock)

    if not registered:
        print("[!] Impossibile registrarsi. Proseguo in modalità listen-only.")

    # Loop principale — attendi chiamate
    print(f"\n[*] In attesa di chiamate in ingresso...")
    print(f"[*] Auto-answer: ABILITATO")
    print(f"[*] Premi Ctrl+C per terminare\n")

    sock.settimeout(None)  # Blocco indefinito
    call_count = 0

    try:
        while True:
            data, addr = sock.recvfrom(4096)
            message = data.decode('utf-8', errors='replace')
            first_line = message.split('\r\n')[0] if message else ""

            # Gestisci INVITE in ingresso
            if first_line.startswith('INVITE '):
                call_count += 1
                print(f"\n[*] Chiamata #{call_count} ricevuta da {addr}")
                handle_incoming_invite(sock, data, addr)

            # Gestisci OPTIONS (keepalive)
            elif first_line.startswith('OPTIONS '):
                # Rispondi con 200 OK
                ok = (
                    f"SIP/2.0 200 OK\r\n"
                    f"Content-Length: 0\r\n\r\n"
                )
                sock.sendto(ok.encode(), addr)

            # Gestisci BYE
            elif first_line.startswith('BYE '):
                print(f"\n[*] BYE ricevuto — chiamata terminata")
                ok = (
                    f"SIP/2.0 200 OK\r\n"
                    f"Content-Length: 0\r\n\r\n"
                )
                sock.sendto(ok.encode(), addr)

            # Gestisci ACK
            elif first_line.startswith('ACK '):
                print(f"[<] ACK ricevuto — sessione confermata")

            # Ignora altre risposte
            else:
                if first_line:
                    print(f"[<] {first_line[:80]}")

    except KeyboardInterrupt:
        print("\n\n[*] Terminazione richiesta. Chiusura...")
    finally:
        sock.close()
        print(f"[*] Totale chiamate ricevute: {call_count}")


if __name__ == "__main__":
    main()
