# HarmonyByMAGNA

<p align="center">
  <img src="https://img.shields.io/badge/Magna%20International-Turkey-red?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Platform-Production%20Logistics-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge" />
</p>

> **Magna Türkiye için tasarlanmış, Magna IT Türkiye ekibi tarafından geliştirilen entegre lojistik ve üretim takip platformu.**

---

## 🏢 Hakkında

**HarmonyByMAGNA**, Magna International'ın Türkiye fabrikalarındaki JIT (Just-In-Time) üretim süreçlerini uçtan uca dijitalleştirmek amacıyla geliştirilmiş bir yazılım ekosistemidir. Dolly takibinden sevkiyat yönetimine, forklift operasyonlarından yönetici analizlerine kadar tüm üretim ve lojistik süreçleri tek bir çatı altında toplar.

**Geliştirici:** Magna IT Türkiye Ekibi  
**Hedef:** Magna Türkiye üretim tesisleri  
**Mimari:** Mikroservis tabanlı, çok katmanlı platform

---

## 🗂️ Proje Yapısı

Harmony ekosistemi dört ana bileşenden oluşmaktadır:

```
HarmonyByMAGNA/
├── HarmonyEcoSystem/           # Ana backend & Control Tower
├── HarmonyEcoSystemTrixServices/  # Windows servisleri (EOL entegrasyonu)
├── HarmonyMobileApp(elterminali)/ # Android el terminali uygulaması
└── HarmonyView/                # Yönetici & operatör dashboard'ları
```

---

## 📦 Bileşenler

### 1. HarmonyEcoSystem — Control Tower Backend

Flask tabanlı ana backend sistemi. Magna üretim hattındaki dolly'lerin (parça taşıma arabaları) lojistik takibini sağlar.

**Teknolojiler:** Python, Flask, SQL Server, REST API, JWT Authentication

**Temel Özellikler:**
- Dolly yaşam döngüsü yönetimi (oluşturma → yükleme → sevkiyat)
- Forklift operatörleri için barkod tabanlı kimlik doğrulama
- Web Dashboard üzerinden sefer no + plaka girişi ve ASN/İrsaliye gönderimi
- Gerçek zamanlı sıra yönetimi ve sayfalama
- Admin/Operatör rollü kullanıcı yönetimi
- Analitik modülü ile üretim verisi raporlama
- Nginx + Gunicorn ile production-ready deploy

**İş Akışı:**
```
EOL İstasyonu → Dolly çıkar
    ↓
Forklift (Android) → Çalışan barkodu ile giriş
    ↓
Forklift (Android) → Dolly'leri sırayla okut (TIR'a yükleme)
    ↓
Forklift (Android) → "Yükleme Tamamlandı"
    ↓
Web Operatör → Sefer No + Plaka + ASN/İrsaliye → Gönder
    ↓
Sistem → SeferDollyEOL tablosuna kaydet ✅
```

---

### 2. HarmonyEcoSystemTrixServices — Windows EOL Servisleri

Trix/EOL istasyonları ile ana sistem arasında köprü görevi gören Windows background servisleri.

**Teknolojiler:** Python, Windows Service, SQL Server

**Temel Özellikler:**
- EOL istasyonlarından dolly verilerini otomatik çeken servis
- Windows Service olarak çalışma (otomatik başlatma / yeniden başlatma)
- Konfigürasyona dayalı esnek yapı (`config.json`)
- Servis kurulum ve kaldırma scriptleri (`.bat`)

---

### 3. HarmonyMobileApp — Android El Terminali

Forklift operatörlerinin sahada kullandığı Android tabanlı el terminali uygulaması. Kiosk modunda çalışacak şekilde tasarlanmıştır.

**Teknolojiler:** Kotlin, Android, Retrofit, Kiosk Mode

**Temel Özellikler:**
- Çalışan barkodu ile güvenli giriş (JWT token)
- Dolly barkodlarını sırayla okutarak TIR yükleme
- "Yükleme Tamamlandı" akışı ile backend'e otomatik bildirim
- Kiosk modu: uygulama dışına çıkışı engelleyen güvenli çalışma ortamı
- HarmonyEcoSystem REST API ile tam entegrasyon

---

### 4. HarmonyView — Yönetici & Operatör Dashboard'ları

JIT üretim sevkiyat takibi, analiz ve görselleştirme için geliştirilmiş web tabanlı dashboard sistemi.

**Teknolojiler:** React, Vite, Tailwind CSS, Python (Flask backend), SQL Server

**Temel Özellikler:**
- Gerçek zamanlı üretim ve sevkiyat takibi
- Manager Dashboard: üretim hattından sevkiyata tüm süreçlerin özet görünümü
- Operatör paneli: günlük iş takibi ve görev yönetimi
- TV/büyük ekran modu: fabrika içi bilgi ekranları için optimize edilmiş görünüm
- SQL View tabanlı veri sorguları ile yüksek performanslı raporlama
- Chatbot entegrasyonu (natural language ile veri sorgulama)

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Backend | Python, Flask, Gunicorn |
| Veritabanı | Microsoft SQL Server |
| Frontend | React, Vite, Tailwind CSS |
| Mobil | Android (Java) |
| Servisler | Windows Service (Python) |
| Sunucu | Nginx, Linux (systemd) |
| Kimlik Doğrulama | JWT (Bearer Token) |

---

## 🚀 Kurulum

Her bileşenin kendi dizininde detaylı kurulum kılavuzu bulunmaktadır:

- **HarmonyEcoSystem:** [`HarmonyEcoSystem/README.md`](HarmonyEcoSystem/README.md)
- **HarmonyView:** [`HarmonyView/harmonyview/README.md`](HarmonyView/harmonyview/README.md)
- **HarmonyMobileApp:** [`HarmonyMobileApp(elterminali)/ControlTower/`](HarmonyMobileApp(elterminali)/ControlTower/)
- **TrixServices:** [`HarmonyEcoSystemTrixServices/DollyEOLService/`](HarmonyEcoSystemTrixServices/DollyEOLService/)

---

## 👥 Geliştirici Ekip

**Magna IT Türkiye Ekibi**  
Magna International — Türkiye Operasyonları

---

## 📄 Lisans

Bu proje Magna International bünyesinde geliştirilmiş olup şirket içi kullanıma yöneliktir. Detaylar için [`LICENSE`](LICENSE) dosyasına bakınız.
