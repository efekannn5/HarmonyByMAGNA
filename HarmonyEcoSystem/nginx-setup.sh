#!/bin/bash

# Nginx Reverse Proxy Kurulum Scripti
# Bu script ymcHarmony.magna.global -> localhost:8181 yönlendirmesi yapar

echo "=== Nginx Kurulumu Başlıyor ==="

# Nginx yüklü mü kontrol et
if ! command -v nginx &> /dev/null; then
    echo "Nginx yükleniyor..."
    sudo apt update
    sudo apt install -y nginx
else
    echo "Nginx zaten yüklü"
fi

# Nginx config dosyası oluştur
echo "Nginx konfigürasyonu oluşturuluyor..."

sudo tee /etc/nginx/sites-available/harmonyecosystem > /dev/null <<'EOF'
server {
    listen 80;
    server_name ymcharmony.magna.global;

    # Log dosyaları
    access_log /var/log/nginx/harmony_access.log;
    error_log /var/log/nginx/harmony_error.log;

    # Client body size limit (büyük dosya yüklemeleri için)
    client_max_body_size 50M;

    location / {
        # Port 8181'e yönlendir
        proxy_pass http://127.0.0.1:8181;
        
        # Gerekli header'lar
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket desteği (eğer gerekirse)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout ayarları
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

# Symbolic link oluştur
if [ -f /etc/nginx/sites-enabled/harmonyecosystem ]; then
    echo "Config zaten aktif"
else
    echo "Config aktifleştiriliyor..."
    sudo ln -s /etc/nginx/sites-available/harmonyecosystem /etc/nginx/sites-enabled/
fi

# Default site'ı devre dışı bırak (isteğe bağlı)
if [ -f /etc/nginx/sites-enabled/default ]; then
    echo "Default site devre dışı bırakılıyor..."
    sudo rm /etc/nginx/sites-enabled/default
fi

# Nginx config test et
echo "Nginx konfigürasyonu test ediliyor..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx restart ediliyor..."
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    echo ""
    echo "=== Kurulum Tamamlandı! ==="
    echo ""
    echo "✅ Port 80'de Nginx reverse proxy çalışıyor"
    echo "✅ ymcHarmony.magna.global -> localhost:8181 yönlendirmesi aktif"
    echo "✅ Cihazlar 10.19.236.29:8181 ile çalışmaya devam edebilir"
    echo ""
    echo "Test etmek için:"
    echo "  curl http://ymcharmony.magna.global"
    echo ""
    echo "Nginx durumu:"
    sudo systemctl status nginx --no-pager
else
    echo "❌ Nginx konfigürasyonunda hata var!"
    exit 1
fi
