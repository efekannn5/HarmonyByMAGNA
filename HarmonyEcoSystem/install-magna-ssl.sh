#!/bin/bash

# Magna IT'den gelen SSL sertifikalarını kurma scripti
# IT'den aldığınız dosyaları /ssl klasörüne koyun ve bu scripti çalıştırın

echo "=== Magna IT SSL Sertifikası Kurulumu ==="

SSL_DIR="/home/ymc_harmony/Harmony/HarmonyEcoSystem/HarmonyEcoSystem/ssl"

# Gerekli dosyaları kontrol et
echo "Gerekli dosyalar kontrol ediliyor..."

MISSING=0

if [ ! -f "$SSL_DIR/server.crt" ] && [ ! -f "$SSL_DIR/cert.pem" ]; then
    echo "❌ Server Certificate bulunamadı (server.crt veya cert.pem)"
    echo "   Lütfen IT'den aldığınız sertifikayı $SSL_DIR/server.crt olarak kaydedin"
    MISSING=1
fi

if [ ! -f "$SSL_DIR/server.key" ] && [ ! -f "$SSL_DIR/key.pem" ]; then
    echo "❌ Private Key bulunamadı (server.key veya key.pem)"
    echo "   Lütfen IT'den aldığınız key dosyasını $SSL_DIR/server.key olarak kaydedin"
    MISSING=1
fi

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "Dosyaları şu şekilde yerleştirin:"
    echo "  1. Server Certificate -> $SSL_DIR/server.crt"
    echo "  2. Private Key -> $SSL_DIR/server.key"
    echo "  3. Intermediate Chain -> $SSL_DIR/intermediate.crt (varsa)"
    echo "  4. Root CA -> $SSL_DIR/root-ca.crt (opsiyonel)"
    exit 1
fi

# Dosya isimlerini standartlaştır
if [ -f "$SSL_DIR/cert.pem" ] && [ ! -f "$SSL_DIR/server.crt" ]; then
    cp "$SSL_DIR/cert.pem" "$SSL_DIR/server.crt"
fi

if [ -f "$SSL_DIR/key.pem" ] && [ ! -f "$SSL_DIR/server.key" ]; then
    cp "$SSL_DIR/key.pem" "$SSL_DIR/server.key"
fi

# Intermediate chain varsa birleştir
if [ -f "$SSL_DIR/intermediate.crt" ]; then
    echo "Intermediate certificate bulundu, birleştiriliyor..."
    cat "$SSL_DIR/server.crt" "$SSL_DIR/intermediate.crt" > "$SSL_DIR/fullchain.crt"
    CERT_FILE="$SSL_DIR/fullchain.crt"
else
    CERT_FILE="$SSL_DIR/server.crt"
fi

echo "✅ Tüm dosyalar hazır"

# Nginx config oluştur
echo "Nginx HTTPS konfigürasyonu oluşturuluyor..."

sudo tee /etc/nginx/sites-available/harmonyecosystem > /dev/null <<EOF
# HTTP -> HTTPS yönlendirme
server {
    listen 80;
    server_name ymcharmony.magna.global;
    return 301 https://\$host\$request_uri;
}

# HTTPS Server - Magna IT SSL Sertifikası
server {
    listen 443 ssl http2;
    server_name ymcharmony.magna.global;

    # Magna IT SSL Sertifikaları
    ssl_certificate $CERT_FILE;
    ssl_certificate_key $SSL_DIR/server.key;

    # SSL Güvenlik Ayarları
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Log dosyaları
    access_log /var/log/nginx/harmony_access.log;
    error_log /var/log/nginx/harmony_error.log;

    # Client body size limit
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
        
        # WebSocket desteği
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout ayarları
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

# Symbolic link güncelle
if [ -L /etc/nginx/sites-enabled/harmonyecosystem ]; then
    sudo rm /etc/nginx/sites-enabled/harmonyecosystem
fi
sudo ln -s /etc/nginx/sites-available/harmonyecosystem /etc/nginx/sites-enabled/

# Nginx test
echo "Nginx konfigürasyonu test ediliyor..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx restart ediliyor..."
    sudo systemctl restart nginx
    
    echo ""
    echo "=== ✅ Magna IT SSL Kurulumu Tamamlandı! ==="
    echo ""
    echo "🔒 Sertifika Detayları:"
    openssl x509 -in $CERT_FILE -noout -subject -issuer -dates
    echo ""
    echo "✅ Kullanıcılar artık uyarı OLMADAN erişebilir:"
    echo "   https://ymcharmony.magna.global"
    echo ""
    echo "✅ Cihazlar için değişiklik yok:"
    echo "   10.19.236.29:8181"
    echo ""
else
    echo "❌ Nginx konfigürasyonunda hata var!"
    exit 1
fi
