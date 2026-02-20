#!/bin/bash

# HTTP-only Nginx Config (SSL uyarısı olmadan)
# Geçici çözüm olarak sadece HTTP kullanılır

echo "=== HTTP-Only Nginx Kurulumu ==="

sudo tee /etc/nginx/sites-available/harmonyecosystem > /dev/null <<'EOF'
# Sadece HTTP Server (SSL yok)
server {
    listen 80;
    server_name ymcharmony.magna.global;

    # Log dosyaları
    access_log /var/log/nginx/harmony_access.log;
    error_log /var/log/nginx/harmony_error.log;

    # Client body size limit
    client_max_body_size 50M;

    location / {
        # Port 8181'e yönlendir
        proxy_pass http://127.0.0.1:8181;
        
        # Gerekli header'lar
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket desteği
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

echo "Nginx restart ediliyor..."
sudo systemctl restart nginx

echo ""
echo "=== HTTP-Only Mod Aktif ==="
echo ""
echo "✅ Kullanıcılar artık SSL uyarısı OLMADAN erişebilir:"
echo "   http://ymcharmony.magna.global"
echo ""
echo "⚠️  NOT: Bu geçici çözümdür. Güvenlik için HTTPS önerilir."
echo "   Magna IT'den internal SSL sertifikası talep edin."
echo ""
