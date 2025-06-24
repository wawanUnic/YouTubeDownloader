#!/bin/bash
LOG_FILE="/root/haproxy_cert_update.log"

CERT_DIR="/etc/letsencrypt/live"
HAPROXY_CERT_DIR="/etc/haproxy/certs"
DOMAINS=("youtubedownloader.by")

echo "[$(date)] Starting certificate update..." >> "$LOG_FILE"

for domain in "${DOMAINS[@]}"; do
    if [ -f "$CERT_DIR/$domain/fullchain.pem" ] && [ -f "$CERT_DIR/$domain/privkey.pem" ]; then
        cat "$CERT_DIR/$domain/fullchain.pem" "$CERT_DIR/$domain/privkey.pem" > "$HAPROXY_CERT_DIR/$domain.pem"
        echo "[$(date)] Certificate for $domain updated successfully." >> "$LOG_FILE"
    else
        echo "[$(date)] ERROR: Certificate files for $domain are missing!" >> "$LOG_FILE"
    fi
done

# Проверка конфигурации HAProxy
haproxy -c -f /etc/haproxy/haproxy.cfg >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    rc-service haproxy reload >> "$LOG_FILE" 2>&1
    echo "[$(date)] HAProxy reloaded successfully." >> "$LOG_FILE"
else
    echo "[$(date)] ERROR: Invalid HAProxy configuration." >> "$LOG_FILE"
fi

echo "[$(date)] Certificate update process finished." >> "$LOG_FILE"
