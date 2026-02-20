# ACİL DURUM ADB KOMUTLARI
## Kiosk Modunda Test Sırasında Kullanılacak Komutlar

---

## 🔴 ACİL ÇIKIŞ - Kiosk Modundan Çık
```bash
# Lock task mode'u durdur
adb shell am task lock stop

# Device Owner'ı kaldır (kalıcı çözüm)
adb shell dpm remove-active-admin com.magna.controltower/.KioskModeReceiver
```

---

## 📶 WiFi Sorunları

### WiFi Açma/Kapama
```bash
# WiFi'yi kapat
adb shell svc wifi disable

# WiFi'yi aç
adb shell svc wifi enable

# WiFi durumunu kontrol et
adb shell dumpsys wifi | grep "Wi-Fi is"
```

### WiFi Yeniden Başlat
```bash
# WiFi restart
adb shell svc wifi disable && sleep 2 && adb shell svc wifi enable
```

### WiFi Ağlarını Listele
```bash
# Kayıtlı WiFi ağları
adb shell cmd wifi list-networks

# Mevcut bağlantı durumu
adb shell dumpsys wifi | grep "mNetworkInfo"
```

### Belirli WiFi'a Bağlan (WiFi ayarlarını aç)
```bash
adb shell am start -a android.settings.WIFI_SETTINGS
```

---

## 🔄 Uygulama Sorunları

### Uygulamayı Yeniden Başlat
```bash
# Uygulamayı kapat
adb shell am force-stop com.magna.controltower

# Uygulamayı başlat
adb shell am start -n com.magna.controltower/.AuthActivity
```

### Uygulama Çöktüyse
```bash
# Crash log'u göster
adb logcat -d | grep "AndroidRuntime"

# Uygulama state'ini temizle ve başlat
adb shell pm clear com.magna.controltower
adb shell am start -n com.magna.controltower/.AuthActivity
```

### Session/Cache Temizleme (Verileri silmeden)
```bash
# Sadece cache temizle
adb shell pm clear-cache com.magna.controltower
```

---

## 🖥️ Ekran Sorunları

### Ekranı Aç/Kapat
```bash
# Ekranı aç
adb shell input keyevent KEYCODE_WAKEUP

# Ekranı kapat
adb shell input keyevent KEYCODE_SLEEP

# Ekran kilidi açma (swipe up)
adb shell input swipe 300 1000 300 300
```

### Ekran Parlaklığı
```bash
# Parlaklığı maksimuma çıkar (0-255)
adb shell settings put system screen_brightness 255

# Otomatik parlaklığı kapat
adb shell settings put system screen_brightness_mode 0
```

### Ekran Timeout (Ekran kapanma süresi)
```bash
# Ekranı sürekli açık tut (timeout: maksimum - 30 dakika milisaniye olarak)
adb shell settings put system screen_off_timeout 2147483647
```

---

## 🔊 Ses Sorunları

### Ses Seviyesi
```bash
# Medya sesini maksimuma çıkar
adb shell media volume --stream 3 --set 15

# Tüm sesleri kontrol et
adb shell dumpsys audio | grep "volume"
```

### Sessiz Mod
```bash
# Sessiz modu kapat
adb shell cmd notification set_dnd off
```

---

## 🔐 Backend API Bağlantı Sorunları

### Backend'e Ping At
```bash
# Backend erişilebilir mi kontrol et
adb shell ping -c 3 10.25.64.181
```

### Test API İsteği Gönder
```bash
# Login endpoint'ini test et (curl varsa)
adb shell curl -X POST http://10.25.64.181:8181/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"barcode":"TEST_BARKOD"}'
```

### Network İstatistikleri
```bash
# Aktif bağlantıları göster
adb shell netstat | grep 10.25.64.181
```

---

## 🔋 Pil ve Performans

### Pil Durumu
```bash
# Pil yüzdesi ve durumu
adb shell dumpsys battery | grep level

# Şarj durumu
adb shell dumpsys battery | grep status
```

### Performans Sorunları
```bash
# CPU ve bellek kullanımı
adb shell top -n 1 | grep com.magna.controltower

# Bellek durumu
adb shell dumpsys meminfo com.magna.controltower
```

### Cihazı Yeniden Başlat
```bash
# Reboot (son çare)
adb reboot
```

---

## 📱 Cihaz Bilgileri

### Cihaz Durumu
```bash
# Android versiyonu
adb shell getprop ro.build.version.release

# Cihaz modeli
adb shell getprop ro.product.model

# Ekran çözünürlüğü
adb shell wm size

# Ekran yoğunluğu
adb shell wm density
```

### Yüklü Uygulamalar
```bash
# Uygulama yüklü mü kontrol et
adb shell pm list packages | grep controltower

# Uygulama versiyonu
adb shell dumpsys package com.magna.controltower | grep versionName
```

---

## 🗂️ Log ve Debug

### Gerçek Zamanlı Loglar
```bash
# Sadece uygulama logları (filtreli)
adb logcat | grep "ControlTower"

# Hata logları
adb logcat *:E

# Tüm logları temizle ve yeniden başlat
adb logcat -c && adb logcat
```

### Crash Raporu Al
```bash
# Son crash'i göster
adb logcat -d | grep -A 50 "AndroidRuntime: FATAL"

# Tüm logları dosyaya kaydet
adb logcat -d > /Users/efeknefe/Desktop/device_logs.txt
```

---

## 🛠️ Ayarlar Ekranlarına Erişim

### Sistem Ayarları
```bash
# Ana ayarlar
adb shell am start -a android.settings.SETTINGS

# WiFi ayarları
adb shell am start -a android.settings.WIFI_SETTINGS

# Geliştirici ayarları
adb shell am start -a android.settings.APPLICATION_DEVELOPMENT_SETTINGS

# Uygulama yöneticisi
adb shell am start -a android.settings.APPLICATION_SETTINGS
```

---

## 📥 Acil APK Güncelleme

### Yeni APK Yükle
```bash
# Derle
./gradlew assembleDebug

# Eski versiyonu kaldırmadan yükle
adb install -r app/build/outputs/apk/debug/app-debug.apk

# Kaldır ve yeni versiyonu yükle (tüm veriler silinir)
adb uninstall com.magna.controltower
adb install app/build/outputs/apk/debug/app-debug.apk
```

---

## 🚨 KURTARMA SENARYOLARı

### Senaryo 1: Uygulama Dondu, Çıkış Yok
```bash
adb shell am task lock stop
adb shell am force-stop com.magna.controltower
adb shell am start -n com.magna.controltower/.AuthActivity
```

### Senaryo 2: WiFi Bağlantısı Kesildi
```bash
adb shell svc wifi disable
sleep 3
adb shell svc wifi enable
sleep 5
adb shell ping -c 3 10.25.64.181
```

### Senaryo 3: Backend Yanıt Vermiyor
```bash
# Backend'i ping'le
adb shell ping -c 5 10.25.64.181

# DNS kontrol et
adb shell nslookup 10.25.64.181

# Uygulamayı yeniden başlat
adb shell am force-stop com.magna.controltower
adb shell am start -n com.magna.controltower/.AuthActivity
```

### Senaryo 4: Ekran Karardı / Yanıt Vermiyor
```bash
adb shell input keyevent KEYCODE_WAKEUP
adb shell input swipe 300 1000 300 300
adb shell input keyevent KEYCODE_HOME
adb shell am start -n com.magna.controltower/.AuthActivity
```

### Senaryo 5: Session Bozuldu / Giriş Yapamıyor
```bash
# Uygulama verilerini temizle
adb shell pm clear com.magna.controltower

# Yeniden başlat
adb shell am start -n com.magna.controltower/.AuthActivity
```

### Senaryo 6: Tamamen Kilitlendi, Hiçbir Şey Çalışmıyor
```bash
# Device Owner'ı kaldır
adb shell dpm remove-active-admin com.magna.controltower/.KioskModeReceiver

# Lock task mode'dan çık
adb shell am task lock stop

# Uygulamayı kapat
adb shell am force-stop com.magna.controltower

# Son çare: cihazı yeniden başlat
adb reboot
```

---

## 📋 Hızlı Referans - En Çok Kullanılanlar

```bash
# ⚡ Kiosk modundan çık
adb shell am task lock stop

# ⚡ Uygulamayı yeniden başlat
adb shell am force-stop com.magna.controltower && adb shell am start -n com.magna.controltower/.AuthActivity

# ⚡ WiFi restart
adb shell svc wifi disable && sleep 2 && adb shell svc wifi enable

# ⚡ Backend ping
adb shell ping -c 3 10.25.64.181

# ⚡ Logları izle
adb logcat | grep "ControlTower"

# ⚡ Ekranı aç
adb shell input keyevent KEYCODE_WAKEUP

# ⚡ Session temizle
adb shell pm clear com.magna.controltower
```

---

## 💡 İpuçları

1. **Birden fazla cihaz bağlıysa**: Komutların başına `-s DEVICE_ID` ekle
   ```bash
   adb devices  # Cihaz ID'sini bul
   adb -s ABC123456 shell am task lock stop
   ```

2. **Komutları script yap**: Sık kullanılanları .sh dosyası yap
   ```bash
   chmod +x emergency_restart.sh
   ./emergency_restart.sh
   ```

3. **Remote ADB**: Kablosuz bağlantı için
   ```bash
   adb tcpip 5555
   adb connect 192.168.1.XXX:5555
   ```

4. **Log dosyası oluştur**: Her testte logları kaydet
   ```bash
   adb logcat -d > logs/test_$(date +%Y%m%d_%H%M%S).txt
   ```
