#!/bin/bash

# Nginx HTTPS Reverse Proxy Kurulum Scripti
# Bu script ymcHarmony.magna.global -> localhost:8181 HTTPS yönlendirmesi yapar

echo "=== Nginx HTTPS Kurulumu Başlıyor ==="

# Nginx yüklü mü kontrol et
if ! command -v nginx &> /dev/null; then
    echo "Nginx yükleniyor..."
    sudo apt update
    sudo apt install -y nginx
else
    echo "Nginx zaten yüklü"
fi

# SSL sertifikalarını kontrol et
SSL_DIR="/home/ymc_harmony/Harmony/HarmonyEcoSystem/HarmonyEcoSystem/ssl"
if [ ! -f "$SSL_DIR/cert.pem" ] || [ ! -f "$SSL_DIR/key.pem" ]; then
    echo "❌ SSL sertifikaları bulunamadı: $SSL_DIR"
    exit 1
fi

echo "✅ SSL sertifikaları bulundu"

# Nginx config dosyası oluştur
echo "Nginx HTTPS konfigürasyonu oluşturuluyor..."

sudo tee /etc/nginx/sites-available/harmonyecosystem > /dev/null <<EOF
# HTTP -> HTTPS yönlendirme
server {
    listen 80;
    server_name ymcharmony.magna.global;

    # Tüm HTTP isteklerini HTTPS'e yönlendir
    return 301 https://\$host\$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name ymcharmony.magna.global;

    # SSL Sertifikaları
    ssl_certificate $SSL_DIR/cert.pem;
    ssl_certificate_key $SSL_DIR/key.pem;

    # SSL Güvenlik Ayarları
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Log dosyaları
    access_log /var/log/nginx/harmony_access.log;
    error_log /var/log/nginx/harmony_error.log;

    # Client body size limit (büyük dosya yüklemeleri için)
    client_max_body_size 50M;

    location / {
        # Port 8181'e yönlendir
        proxy_pass http://127.0.0.1:8181;
        
        # Gerekli header'lar
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Port \$server_port;
        
        # WebSocket desteği (eğer gerekirse)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout ayarları
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}

# IP:8181 erişimini engelleme (opsiyonel - cihazlar için açık bırakıyoruz)
# Eğer sadece HTTPS erişim istiyorsanız, bu bloğu aktif edin
# server {
#     listen 8181;
#     server_name ymcharmony.magna.global;
#     return 444;  # Bağlantıyı kapat
# }
EOF

# Symbolic link oluştur
if [ -L /etc/nginx/sites-enabled/harmonyecosystem ]; then
    echo "Eski config kaldırılıyor..."
    sudo rm /etc/nginx/sites-enabled/harmonyecosystem
fi

echo "Config aktifleştiriliyor..."
sudo ln -s /etc/nginx/sites-available/harmonyecosystem /etc/nginx/sites-enabled/

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
    echo "=== HTTPS Kurulum Tamamlandı! ==="
    echo ""
    echo "✅ Port 80: HTTP -> HTTPS yönlendirme aktif"
    echo "✅ Port 443: HTTPS -> localhost:8181 yönlendirmesi aktif"
    echo "✅ SSL Sertifikaları: $SSL_DIR/cert.pem"
    echo "✅ Cihazlar 10.19.236.29:8181 ile çalışmaya devam edebilir"
    echo ""
    echo "Kullanıcılar artık şu şekilde erişebilir:"
    echo "  https://ymcharmony.magna.global (önerilen)"
    echo "  http://ymcharmony.magna.global (otomatik HTTPS'e yönlendirilir)"
    echo ""
    echo "Cihazlar için değişiklik yok:"
    echo "  10.19.236.29:8181 (aynen çalışmaya devam eder)"
    echo ""
    echo "Test etmek için:"
    echo "  curl -k https://ymcharmony.magna.global"
    echo ""
    echo "Nginx durumu:"
    sudo systemctl status nginx --no-pager
else
    echo "❌ Nginx konfigürasyonunda hata var!"
    exit 1
fi
