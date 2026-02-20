#!/bin/bash

# HarmonyEcoSystem Systemd Servis Kurulum Scripti
# Bu script servisi yükler ve başlatır

set -e

SERVICE_NAME="harmonyecosystem"
SERVICE_FILE="$SERVICE_NAME.service"
SYSTEMD_PATH="/etc/systemd/system/$SERVICE_FILE"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "HarmonyEcoSystem Servis Kurulumu"
echo "=========================================="

# Root kontrolü
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Bu scripti sudo ile çalıştırmalısınız!"
    echo "Kullanım: sudo bash $0"
    exit 1
fi

# Gunicorn kurulu mu kontrol et
if ! command -v gunicorn &> /dev/null; then
    echo "⚠️  Gunicorn bulunamadı. Yükleniyor..."
    pip3 install gunicorn
else
    echo "✓ Gunicorn kurulu"
fi

# Logs klasörünü oluştur
if [ ! -d "$CURRENT_DIR/logs" ]; then
    echo "📁 Logs klasörü oluşturuluyor..."
    mkdir -p "$CURRENT_DIR/logs"
    chown sua_it_ai:sua_it_ai "$CURRENT_DIR/logs"
fi

# Servis dosyasını kopyala
echo "📋 Servis dosyası kopyalanıyor..."
cp "$CURRENT_DIR/$SERVICE_FILE" "$SYSTEMD_PATH"

# Systemd'yi yeniden yükle
echo "🔄 Systemd yeniden yükleniyor..."
systemctl daemon-reload

# Servisi etkinleştir
echo "✅ Servis etkinleştiriliyor..."
systemctl enable $SERVICE_NAME

# Servisi başlat
echo "🚀 Servis başlatılıyor..."
systemctl start $SERVICE_NAME

# Durum kontrolü
echo ""
echo "=========================================="
echo "📊 Servis Durumu:"
echo "=========================================="
systemctl status $SERVICE_NAME --no-pager

echo ""
echo "=========================================="
echo "✅ Kurulum Tamamlandı!"
echo "=========================================="
echo ""
echo "Kullanabileceğiniz komutlar:"
echo "  • Servisi başlat:    sudo systemctl start $SERVICE_NAME"
echo "  • Servisi durdur:    sudo systemctl stop $SERVICE_NAME"
echo "  • Servisi yeniden başlat: sudo systemctl restart $SERVICE_NAME"
echo "  • Servis durumu:     sudo systemctl status $SERVICE_NAME"
echo "  • Logları görüntüle: sudo journalctl -u $SERVICE_NAME -f"
echo "  • Servisi devre dışı bırak: sudo systemctl disable $SERVICE_NAME"
echo ""
