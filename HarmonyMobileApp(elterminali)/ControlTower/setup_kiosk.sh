#!/bin/bash

# Device Owner Kiosk Modu Kurulum Scripti
# ========================================

echo "🔧 Harmony Mobile - Kiosk Modu Kurulumu"
echo "========================================"
echo ""

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}⚠️  ÖNEMLİ UYARILAR:${NC}"
echo "1. Cihazda hiçbir Google hesabı olmamalı"
echo "2. Cihaz fabrika ayarlarına dönmüş olmalı"
echo "3. USB debugging açık olmalı"
echo "4. Uygulama yüklü olmalı"
echo ""
read -p "Devam etmek istiyor musunuz? (e/h): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Ee]$ ]]
then
    exit 1
fi

echo ""
echo "📱 Cihaz bağlantısı kontrol ediliyor..."
if ! adb devices | grep -q "device$"; then
    echo -e "${RED}❌ Cihaz bulunamadı! USB debugging açık mı?${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Cihaz bağlı${NC}"

echo ""
echo "🔍 Google hesapları kontrol ediliyor..."
ACCOUNTS=$(adb shell dumpsys account | grep -c "Account {")
if [ "$ACCOUNTS" -gt 0 ]; then
    echo -e "${RED}❌ Cihazda $ACCOUNTS hesap var!${NC}"
    echo "Önce tüm hesapları kaldırın veya cihazı fabrika ayarlarına döndürün."
    exit 1
fi
echo -e "${GREEN}✅ Hesap yok${NC}"

echo ""
echo "📦 Uygulama kontrol ediliyor..."
if ! adb shell pm list packages | grep -q "com.magna.controltower"; then
    echo -e "${YELLOW}⚠️  Uygulama yüklü değil, yükleniyor...${NC}"
    ./gradlew assembleDebug
    adb install -r app/build/outputs/apk/debug/app-debug.apk
fi
echo -e "${GREEN}✅ Uygulama yüklü${NC}"

echo ""
echo "👑 Device Owner modu etkinleştiriliyor..."
RESULT=$(adb shell dpm set-device-owner com.magna.controltower/.KioskModeReceiver 2>&1)

if echo "$RESULT" | grep -q "Success"; then
    echo -e "${GREEN}✅ Device Owner modu başarıyla etkinleştirildi!${NC}"
    echo ""
    echo "🎉 Kurulum tamamlandı!"
    echo ""
    echo "Artık şunları yapabilirsiniz:"
    echo "• Uygulama tam ekran kiosk modunda çalışacak"
    echo "• Kullanıcı uygulamadan çıkamayacak"
    echo "• Status bar ve navigation bar gizli olacak"
    echo ""
    echo "Kaldırmak için:"
    echo "  adb shell dpm remove-active-admin com.magna.controltower/.KioskModeReceiver"
else
    echo -e "${RED}❌ Hata oluştu:${NC}"
    echo "$RESULT"
    echo ""
    echo "Yaygın hatalar:"
    echo "• 'Not allowed to set the device owner' - Cihazda hesap var"
    echo "• 'Device already provisioned' - Cihaz kullanımda, fabrika ayarlarına dönmeli"
    echo "• 'Unknown admin' - Uygulama düzgün yüklenmemiş"
fi
