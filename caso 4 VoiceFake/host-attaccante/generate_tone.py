#!/usr/bin/env python3
"""
============================================================
 Generatore di tono di test per il POC Panic Engine.
 Crea un file WAV in formato G.711 µ-law compatibile
 con lo script attack.py.
============================================================
"""

import struct
import wave
import math
import os

OUTPUT_PATH = "/app/payload/deepfake_voice.wav"
SAMPLE_RATE = 8000   # 8 kHz (standard telefonia)
DURATION    = 5      # secondi
FREQUENCY   = 440    # Hz (La4 — tono di riferimento)
AMPLITUDE   = 16384  # ~50% del range 16-bit


def generate():
    """Genera un file WAV con tono sinusoidale."""
    n_samples = SAMPLE_RATE * DURATION

    print(f"[*] Generazione tono di test:")
    print(f"    Frequenza:   {FREQUENCY} Hz")
    print(f"    Durata:      {DURATION} secondi")
    print(f"    Sample Rate: {SAMPLE_RATE} Hz")
    print(f"    Campioni:    {n_samples}")

    # Genera campioni PCM 16-bit signed little-endian
    samples = []
    for i in range(n_samples):
        value = int(AMPLITUDE * math.sin(2 * math.pi * FREQUENCY * i / SAMPLE_RATE))
        samples.append(struct.pack('<h', value))

    raw_pcm = b''.join(samples)

    # Scrivi file WAV
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with wave.open(OUTPUT_PATH, 'wb') as wf:
        wf.setnchannels(1)       # Mono
        wf.setsampwidth(2)       # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(raw_pcm)

    file_size = os.path.getsize(OUTPUT_PATH)
    print(f"\n[+] File generato: {OUTPUT_PATH}")
    print(f"    Dimensione: {file_size:,} byte")
    print(f"\n[*] Ora puoi eseguire: python /app/attack.py")


if __name__ == "__main__":
    generate()
