#!/bin/bash

echo "🔍 Kiosk Modu Durum Kontrolü"
echo "============================"
echo ""

# Device owner kontrolü
echo "📱 Device Owner durumu:"
OWNER=$(adb shell dpm list-owners 2>&1)
if echo "$OWNER" | grep -q "com.magna.controltower"; then
    echo "✅ Device Owner: AKTIF"
    echo "$OWNER"
else
    echo "❌ Device Owner: AKTIF DEĞİL"
    echo "$OWNER"
    echo ""
    echo "Kurulum için:"
    echo "  ./setup_kiosk.sh"
fi

echo ""
echo "🔒 Lock Task Packages:"
adb shell dumpsys activity activities | grep -A 5 "mLockTaskPackages"

echo ""
echo "📊 Uygulama bilgisi:"
adb shell dumpsys package com.magna.controltower | grep -E "versionName|versionCode"

echo ""
echo "🎯 Lock Task Mode durumu:"
adb shell dumpsys activity activities | grep -i "locktask"
