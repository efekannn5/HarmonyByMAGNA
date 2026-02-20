#!/bin/bash

# Self-signed SSL sertifikasını sistem güvenilir sertifikalar listesine ekler

SSL_CERT="/home/ymc_harmony/Harmony/HarmonyEcoSystem/HarmonyEcoSystem/ssl/cert.pem"

echo "=== SSL Sertifikası Güvenilir Yapılıyor ==="

if [ ! -f "$SSL_CERT" ]; then
    echo "❌ Sertifika bulunamadı: $SSL_CERT"
    exit 1
fi

echo "✅ Sertifika bulundu: $SSL_CERT"

# Ubuntu/Debian için sistem güvenilir sertifikalar klasörüne kopyala
echo "Sertifika sistem güvenilir klasörüne kopyalanıyor..."
sudo cp "$SSL_CERT" /usr/local/share/ca-certificates/harmony-ecosystem.crt

# Güvenilir sertifikaları güncelle
echo "Güvenilir sertifikalar güncelleniyor..."
sudo update-ca-certificates

echo ""
echo "=== Tamamlandı! ==="
echo ""
echo "✅ Sertifika artık sistem tarafından güvenilir"
echo ""
echo "⚠️  NOT: Tarayıcıların sertifikayı tanıması için:"
echo "   1. Tarayıcıyı tamamen kapatıp yeniden açın"
echo "   2. Tarayıcı önbelleğini temizleyin"
echo "   3. Firefox kullanıyorsanız, Firefox kendi sertifika deposu kullanır"
echo ""
echo "Windows ve Mac kullanıcıları için:"
echo "   - cert.pem dosyasını indirip sistem güvenilir sertifikalar listesine eklemeleri gerekir"
echo ""
