# ============================================================
#  Gateway SIP — Asterisk PBX Vulnerabile
#  Immagine: Alpine 3.19 + Asterisk (PJSIP integrato)
# ============================================================
FROM alpine:3.19

RUN apk update && apk add --no-cache \
    asterisk \
    asterisk-sounds-en \
    asterisk-sample-config \
    && rm -rf /var/cache/apk/*

# Rimuovi config di esempio e sostituisci con i nostri
RUN rm -f /etc/asterisk/pjsip.conf \
          /etc/asterisk/extensions.conf \
          /etc/asterisk/logger.conf \
          /etc/asterisk/modules.conf \
          /etc/asterisk/rtp.conf

COPY pjsip.conf      /etc/asterisk/pjsip.conf
COPY extensions.conf  /etc/asterisk/extensions.conf
COPY logger.conf      /etc/asterisk/logger.conf
COPY modules.conf     /etc/asterisk/modules.conf
COPY rtp.conf         /etc/asterisk/rtp.conf

# Crea directory log con permessi
RUN mkdir -p /var/log/asterisk && \
    chown -R asterisk:asterisk /var/log/asterisk

# Porta SIP + range RTP
EXPOSE 5060/udp
EXPOSE 10000-10100/udp

# Avvio in foreground con output su console
CMD ["asterisk", "-fp"]
