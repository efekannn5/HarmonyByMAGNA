#!/bin/bash

# HarmonyEcoSystem Systemd Servis Kaldırma Scripti

set -e

SERVICE_NAME="harmonyecosystem"
SYSTEMD_PATH="/etc/systemd/system/$SERVICE_NAME.service"

echo "=========================================="
echo "HarmonyEcoSystem Servis Kaldırılıyor"
echo "=========================================="

# Root kontrolü
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Bu scripti sudo ile çalıştırmalısınız!"
    echo "Kullanım: sudo bash $0"
    exit 1
fi

# Servisi durdur
echo "⏹️  Servis durduruluyor..."
systemctl stop $SERVICE_NAME 2>/dev/null || true

# Servisi devre dışı bırak
echo "🔴 Servis devre dışı bırakılıyor..."
systemctl disable $SERVICE_NAME 2>/dev/null || true

# Servis dosyasını sil
if [ -f "$SYSTEMD_PATH" ]; then
    echo "🗑️  Servis dosyası siliniyor..."
    rm "$SYSTEMD_PATH"
fi

# Systemd'yi yeniden yükle
echo "🔄 Systemd yeniden yükleniyor..."
systemctl daemon-reload
systemctl reset-failed 2>/dev/null || true

echo ""
echo "✅ Servis başarıyla kaldırıldı!"
