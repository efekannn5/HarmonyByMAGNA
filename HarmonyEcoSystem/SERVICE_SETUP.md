# HarmonyEcoSystem Systemd Servis Kurulum Kılavuzu

## 📋 Genel Bakış

Bu kılavuz, HarmonyEcoSystem Flask uygulamasını Ubuntu sisteminde systemd servisi olarak çalıştırmanız için gerekli adımları içerir.

## 📁 Oluşturulan Dosyalar

1. **wsgi.py** - WSGI entry point
2. **gunicorn_config.py** - Gunicorn yapılandırması
3. **harmonyecosystem.service** - Systemd servis tanımı
4. **install_service.sh** - Otomatik kurulum scripti
5. **uninstall_service.sh** - Servis kaldırma scripti

## 🚀 Kurulum Adımları

### Yöntem 1: Otomatik Kurulum (Önerilen)

```bash
# 1. Script dosyasını çalıştırılabilir yap
chmod +x install_service.sh

# 2. Scripti sudo ile çalıştır
sudo ./install_service.sh
```

### Yöntem 2: Manuel Kurulum

```bash
# 1. Gunicorn'u yükle (eğer yoksa)
pip3 install gunicorn

# 2. Logs klasörünü oluştur
mkdir -p logs

# 3. Servis dosyasını systemd dizinine kopyala
sudo cp harmonyecosystem.service /etc/systemd/system/

# 4. Systemd'yi yeniden yükle
sudo systemctl daemon-reload

# 5. Servisi etkinleştir (sistem başlangıcında otomatik başlasın)
sudo systemctl enable harmonyecosystem

# 6. Servisi başlat
sudo systemctl start harmonyecosystem

# 7. Servis durumunu kontrol et
sudo systemctl status harmonyecosystem
```

## 🎮 Servis Yönetimi Komutları

```bash
# Servisi başlat
sudo systemctl start harmonyecosystem

# Servisi durdur
sudo systemctl stop harmonyecosystem

# Servisi yeniden başlat
sudo systemctl restart harmonyecosystem

# Servis durumunu görüntüle
sudo systemctl status harmonyecosystem

# Logları canlı izle (systemd logs)
sudo journalctl -u harmonyecosystem -f

# Logları canlı izle (uygulama logs)
tail -f logs/app.log
tail -f logs/gunicorn_error.log

# Servisi devre dışı bırak (sistem başlangıcında başlamasın)
sudo systemctl disable harmonyecosystem

# Servisi etkinleştir (sistem başlangıcında başlasın)
sudo systemctl enable harmonyecosystem
```

## 🗑️ Servisi Kaldırma

```bash
# Otomatik kaldırma scripti
chmod +x uninstall_service.sh
sudo ./uninstall_service.sh

# Manuel kaldırma
sudo systemctl stop harmonyecosystem
sudo systemctl disable harmonyecosystem
sudo rm /etc/systemd/system/harmonyecosystem.service
sudo systemctl daemon-reload
```

## ⚙️ Yapılandırma

### Production vs Development Mode

**harmonyecosystem.service** dosyasında iki seçenek var:

```ini
# Production (Önerilen) - Gunicorn ile
ExecStart=/usr/local/bin/gunicorn --config gunicorn_config.py wsgi:app

# Development (Sadece test için) - Flask built-in server ile
# ExecStart=/usr/bin/python3 run.py
```

### Gunicorn Ayarları (gunicorn_config.py)

```python
workers = 4              # Worker sayısı (CPU sayısı x 2 + 1 önerilir)
bind = '0.0.0.0:8181'   # Port ayarı
timeout = 120            # Request timeout
```

## 📊 Log Dosyaları

- **Systemd logs:** `sudo journalctl -u harmonyecosystem`
- **Uygulama logs:** `logs/app.log`
- **Hata logs:** `logs/app_error.log`
- **Gunicorn access:** `logs/gunicorn_access.log`
- **Gunicorn error:** `logs/gunicorn_error.log`

## 🔧 Sorun Giderme

### Servis başlamıyor?

```bash
# Detaylı hata loglarını kontrol et
sudo journalctl -u harmonyecosystem -n 50 --no-pager

# Servis dosyası syntax kontrolü
sudo systemd-analyze verify harmonyecosystem.service

# Manuel olarak çalıştırıp hataları gör
cd /home/sua_it_ai/controltower/HarmonyEcoSystem
gunicorn --config gunicorn_config.py wsgi:app
```

### Port zaten kullanımda?

```bash
# 8181 portunu kullanan process'i bul
sudo lsof -i :8181

# Process'i kapat
sudo kill -9 <PID>
```

### Dosya izinleri problemi?

```bash
# Doğru kullanıcı ve grup sahipliğini ayarla
sudo chown -R sua_it_ai:sua_it_ai /home/sua_it_ai/controltower/HarmonyEcoSystem
```

## ✅ Kontrol Listesi

- [ ] Gunicorn yüklü mü? (`pip3 list | grep gunicorn`)
- [ ] Logs klasörü var mı?
- [ ] Servis dosyası doğru konumda mı? (`/etc/systemd/system/harmonyecosystem.service`)
- [ ] Dosya izinleri doğru mu?
- [ ] Port 8181 boş mu?
- [ ] Uygulama http://localhost:8181 adresinden erişilebiliyor mu?

## 🌐 Erişim

Servis başarıyla çalışıyorsa:
- **Yerel:** http://localhost:8181
- **Ağ:** http://[SERVER-IP]:8181

## 🔐 Güvenlik Notları

- Production ortamında firewall kurallarını ayarlayın
- Gerekirse nginx/apache reverse proxy kullanın
- SSL/TLS sertifikası ekleyin (Let's Encrypt)
- Database bağlantı bilgilerini environment variables ile yönetin
