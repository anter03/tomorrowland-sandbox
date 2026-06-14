import qrcode

# Inserisci qui l'URL esatto che ti ha fornito GitHub Pages (o usa quello locale per test)
TARGET_URL = "https://anter03.github.io/tomorrowland-sandbox/"
# TARGET_URL = "http://127.0.0.1:5000/promo" # Usa questo per i test in locale

# Generazione del QR Code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)
qr.add_data(TARGET_URL)
qr.make(fit=True)

# Creazione dell'immagine
img = qr.make_image(fill_color="black", back_color="white")
img.save("quishing_payload.png")
print("[+] QR Code malevolo generato con successo: quishing_payload.png")
