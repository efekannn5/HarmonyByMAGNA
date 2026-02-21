# Yazılım Gereksinimleri Tanım Belgesi
# HarmonyByMAGNA — Entegre Lojistik ve Üretim Takip Platformu

---

| Alan | Bilgi |
|------|-------|
| **Belge No** | MAGNA-TR-SRS-001 |
| **Başlık** | HarmonyByMAGNA Yazılım Gereksinimleri Tanım Belgesi |
| **Versiyon** | 1.0.0 |
| **Tarih** | 2026-02-21 |
| **Durum** | Onaylı |
| **Geliştirici** | Magna IT Türkiye Ekibi |
| **Kuruluş** | Magna International — Türkiye Operasyonları |
| **Standart** | ISO/IEC/IEEE 29148:2018 |
| **Gizlilik** | Şirket İçi — Gizli |

---

## Revizyon Geçmişi

| Versiyon | Tarih | Açıklama | Yazar |
|----------|-------|----------|-------|
| 0.1 | 2025-11-01 | İlk taslak | Magna IT Türkiye |
| 0.5 | 2025-11-26 | Forklift kimlik doğrulama modülü eklendi | Magna IT Türkiye |
| 1.0.0 | 2026-02-21 | Onaylı sürüm — Tüm bileşenler dahil | Magna IT Türkiye |

---

## İçindekiler

1. [Giriş](#1-giriş)
   - 1.1 Amaç
   - 1.2 Kapsam
   - 1.3 Tanımlar, Kısaltmalar ve Kısa Adlar
   - 1.4 Atıflar
   - 1.5 Genel Bakış
2. [Genel Tanım](#2-genel-tanım)
   - 2.1 Ürün Perspektifi
   - 2.2 Ürün İşlevleri
   - 2.3 Kullanıcı Sınıfları ve Özellikleri
   - 2.4 Çalışma Ortamı
   - 2.5 Tasarım ve Uygulama Kısıtlamaları
   - 2.6 Kullanıcı Dokümantasyonu
   - 2.7 Varsayımlar ve Bağımlılıklar
3. [Sistem Özellikleri ve Fonksiyonel Gereksinimler](#3-sistem-özellikleri-ve-fonksiyonel-gereksinimler)
   - 3.1 HarmonyEcoSystem — Control Tower Backend
   - 3.2 HarmonyEcoSystemTrixServices — Windows EOL Servisleri
   - 3.3 HarmonyMobileApp — Android El Terminali
   - 3.4 HarmonyView — Yönetici ve Operatör Dashboard'ları
4. [Dış Arayüz Gereksinimleri](#4-dış-arayüz-gereksinimleri)
   - 4.1 Kullanıcı Arayüzleri
   - 4.2 Donanım Arayüzleri
   - 4.3 Yazılım Arayüzleri
   - 4.4 İletişim Arayüzleri
5. [Fonksiyonel Olmayan Gereksinimler](#5-fonksiyonel-olmayan-gereksinimler)
   - 5.1 Performans Gereksinimleri
   - 5.2 Güvenlik Gereksinimleri
   - 5.3 Güvenilirlik ve Erişilebilirlik
   - 5.4 Sürdürülebilirlik
   - 5.5 Taşınabilirlik
6. [Veritabanı Gereksinimleri](#6-veritabanı-gereksinimleri)
   - 6.1 Veri Modeli
   - 6.2 Veri Bütünlüğü
   - 6.3 Veri Saklama ve Arşivleme
7. [Sistem Kısıtlamaları](#7-sistem-kısıtlamaları)
8. [İzlenebilirlik Matrisi](#8-izlenebilirlik-matrisi)
9. [Ekler](#9-ekler)
   - Ek A — API Referansı
   - Ek B — Veritabanı Şeması
   - Ek C — Sözlük

---

## 1. Giriş

### 1.1 Amaç

Bu belge, **HarmonyByMAGNA** entegre lojistik ve üretim takip platformunun yazılım gereksinimlerini ISO/IEC/IEEE 29148:2018 standardına uygun biçimde tanımlar. Belge; sistem mimarları, yazılım geliştiriciler, kalite mühendisleri, proje yöneticileri ve ilgili paydaşlar tarafından referans olarak kullanılmak üzere hazırlanmıştır.

Bu belgenin başlıca amaçları şunlardır:

- Sistemin tüm bileşenlerine ilişkin fonksiyonel ve fonksiyonel olmayan gereksinimleri eksiksiz olarak belgelemek.
- Geliştirme, test ve kabul süreçleri için esas teşkil edecek gereksinim tabanını oluşturmak.
- Paydaşlar arasındaki sistem beklentilerini ortak bir dilde ifade etmek.
- Değişiklik yönetimi ve versiyon kontrolü için izlenebilir bir temel sağlamak.

### 1.2 Kapsam

**HarmonyByMAGNA**, Magna International'ın Türkiye fabrikalarında JIT (Just-In-Time) üretim süreçlerini uçtan uca dijitalleştirmek amacıyla geliştirilmiş bir yazılım ekosistemidir. Platform aşağıdaki dört ana bileşenden oluşur:

| Bileşen | Tanım |
|---------|-------|
| **HarmonyEcoSystem** | Flask tabanlı ana backend ve Control Tower sistemi |
| **HarmonyEcoSystemTrixServices** | EOL istasyonları ile entegrasyon sağlayan Windows servisleri |
| **HarmonyMobileApp** | Forklift operatörlerinin kullandığı Android el terminali uygulaması |
| **HarmonyView** | Yönetici ve operatör web dashboard'ları |

Sistemin kapsamı şu süreçleri içerir:

- Dolly yaşam döngüsü yönetimi (EOL'den sevkiyata kadar)
- Forklift operatörleri için barkod tabanlı kimlik doğrulama
- TIR yükleme ve sevkiyat yönetimi
- ASN (Advance Shipment Notice) ve İrsaliye gönderimi (CEVA entegrasyonu)
- Gerçek zamanlı üretim ve sevkiyat takibi
- Yönetici analitik raporlama

Bu belge kapsamı dışında kalan unsurlar şunlardır:

- CEVA lojistik sisteminin iç işleyişi
- EOL üretim makineleri ve ekipmanları
- Ağ altyapısı ve fiziksel donanım kurulumu

### 1.3 Tanımlar, Kısaltmalar ve Kısa Adlar

| Terim / Kısaltma | Açıklama |
|------------------|----------|
| **API** | Application Programming Interface — Uygulama Programlama Arayüzü |
| **ASN** | Advance Shipment Notice — Ön Sevkiyat Bildirimi |
| **CEVA** | CEVA Logistics — Lojistik hizmet sağlayıcısı |
| **Control Tower** | Dolly lojistiğini izleyen ve yöneten merkezi yönetim sistemi |
| **Dolly** | Üretim hattında parça taşımak için kullanılan tekerlekli taşıma arabası |
| **EOL** | End of Line — Üretim hattı sonu istasyonu |
| **ERP** | Enterprise Resource Planning — Kurumsal Kaynak Planlaması |
| **FIFO** | First In First Out — İlk giren ilk çıkar |
| **GSDB** | Global Supplier Database — Ford Motor Company tedarikçi veri tabanı |
| **GUI** | Graphical User Interface — Grafiksel Kullanıcı Arayüzü |
| **İrsaliye** | Türk lojistik mevzuatına göre mal teslim belgesi |
| **JIT** | Just-In-Time — Tam zamanında üretim yöntemi |
| **JWT** | JSON Web Token — JSON tabanlı kimlik doğrulama belirteci |
| **LIFO** | Last In First Out — Son giren ilk çıkar |
| **ODBC** | Open Database Connectivity — Açık Veritabanı Bağlantısı |
| **REST** | Representational State Transfer — Temsili Durum Transferi |
| **SFR** | Sistem Fonksiyonel Gereksinim (bu belgede gereksinim kodu öneki) |
| **SRS** | Software Requirements Specification — Yazılım Gereksinimleri Tanım Belgesi |
| **SQL** | Structured Query Language — Yapısal Sorgulama Dili |
| **TIR** | Transport International Routier — Uluslararası karayolu taşıma aracı |
| **UAT** | User Acceptance Testing — Kullanıcı Kabul Testi |
| **VIN** | Vehicle Identification Number — Araç Tanımlama Numarası |
| **YAML** | YAML Ain't Markup Language — Yapılandırma dosyası formatı |

### 1.4 Atıflar

| Referans No | Belge / Standart |
|-------------|-----------------|
| [1] | ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering |
| [2] | ISO/IEC 25010:2011 — Systems and Software Engineering — Software Product Quality Requirements and Evaluation (SQuaRE) |
| [3] | ISO/IEC 12207:2017 — Systems and Software Engineering — Software Life Cycle Processes |
| [4] | ISO 9001:2015 — Quality Management Systems — Requirements |
| [5] | RFC 7519 — JSON Web Token (JWT) |
| [6] | RFC 2617 — HTTP Authentication: Basic and Digest Access Authentication |
| [7] | CEVA DT Supplier Web Service Dokümantasyonu (CEVA Logistics, 2024) |
| [8] | Flask Web Framework Documentation v2.3 — https://flask.palletsprojects.com |
| [9] | Android Developer Documentation — https://developer.android.com |
| [10] | Microsoft SQL Server Documentation — https://docs.microsoft.com/sql |

### 1.5 Genel Bakış

Bu belgenin geri kalan bölümleri şu şekilde düzenlenmiştir:

- **Bölüm 2** — Sistemin genel çerçevesini, ürün perspektifini, kullanıcı sınıflarını ve kısıtlamaları tanımlar.
- **Bölüm 3** — Her bileşenin fonksiyonel gereksinimlerini ayrıntılı biçimde açıklar.
- **Bölüm 4** — Dış arayüz gereksinimlerini (kullanıcı, donanım, yazılım, iletişim) kapsar.
- **Bölüm 5** — Performans, güvenlik, güvenilirlik ve sürdürülebilirlik gibi fonksiyonel olmayan gereksinimleri listeler.
- **Bölüm 6** — Veritabanı gereksinimlerini ve veri modelini tanımlar.
- **Bölüm 7** — Sistem kısıtlamalarını belirtir.
- **Bölüm 8** — Gereksinimlerin izlenebilirlik matrisini sunar.
- **Bölüm 9** — API referansını, veritabanı şemasını ve sözlüğü içeren ekleri barındırır.

---

## 2. Genel Tanım

### 2.1 Ürün Perspektifi

HarmonyByMAGNA, mevcut hiçbir sistemden türetilmemiş, sıfırdan geliştirilen bağımsız bir yazılım platformudur. Bununla birlikte şu dış sistemlerle entegre çalışır:

```
┌──────────────────────────────────────────────────────────────────────┐
│                         HarmonyByMAGNA                               │
│                                                                      │
│  ┌─────────────┐   ┌─────────────────┐   ┌────────────────────────┐ │
│  │ HarmonyMobile│   │ HarmonyEcoSystem │   │     HarmonyView        │ │
│  │ App (Android)│◄──│  (Flask/Python) │──►│  (React + Flask)       │ │
│  └──────┬──────┘   └────────┬────────┘   └────────────────────────┘ │
│         │                   │                                        │
│         │          ┌────────▼────────┐                               │
│         │          │  SQL Server DB  │                               │
│         │          │ (ControlTower)  │                               │
│         │          └────────▲────────┘                               │
│         │                   │                                        │
│  ┌──────▼──────┐   ┌────────┴────────┐                               │
│  │  Barkod     │   │  TrixServices   │                               │
│  │  Okuyucu    │   │ (Windows Servis)│                               │
│  └─────────────┘   └─────────────────┘                               │
└──────────────────────────────────────────────────────────────────────┘
          │                   │
          ▼                   ▼
  ┌───────────────┐   ┌──────────────────┐
  │  Fabrika Ağı  │   │  CEVA Logistics  │
  │  (LAN/Wi-Fi)  │   │  (ASN/İrsaliye)  │
  └───────────────┘   └──────────────────┘
```

**Entegrasyon Noktaları:**

| Dış Sistem | Entegrasyon Türü | Amaç |
|------------|-----------------|------|
| CEVA Logistics | SOAP Web Service | ASN ve İrsaliye gönderimi |
| EOL İstasyon Sistemleri | SQL Server (ortak DB veya servis) | Dolly üretim verisi |
| Microsoft SQL Server | ODBC/MSSQL Driver | Birincil veri depolama |
| Android Cihazlar | REST API (HTTP/HTTPS) | Forklift el terminali iletişimi |

### 2.2 Ürün İşlevleri

Sistemin gerçekleştirdiği başlıca işlevler aşağıda özetlenmiştir:

**F-01 Dolly Yaşam Döngüsü Yönetimi**
EOL istasyonundan çıkıştan başlayarak TIR'a yükleme ve sevkiyat onayına kadar dolly'lerin tüm durum geçişlerini yönetir.

**F-02 Forklift Kimlik Doğrulama**
Forklift operatörleri çalışan barkodları aracılığıyla sisteme giriş yapar; tüm işlemler belirli bir kullanıcıya atfedilir.

**F-03 TIR Yükleme Takibi**
Forklift operatörü dolly barkodlarını sırayla okutarak yükleme sırasını kaydeder.

**F-04 Sevkiyat Onayı ve Belgelendirme**
Web operatörü sefer numarası ve plaka bilgisini girerek sevkiyatı onaylar; ASN ve/veya İrsaliye belgesi CEVA sistemine gönderilir.

**F-05 Grup Bazlı EOL Yönetimi**
EOL istasyonları mantıksal gruplara ayrılarak yönetilir; her grup için gönderim etiketi (ASN, İrsaliye veya Her İkisi) tanımlanır.

**F-06 Analitik ve Raporlama**
Üretimden sevkiyata kadar tüm süreçlerin süre analizleri, operatör performans metrikleri ve vardiya bazlı raporlar sunulur.

**F-07 Kullanıcı ve Rol Yönetimi**
Web admin paneli üzerinden kullanıcı hesapları, roller ve terminal cihazları yönetilir.

**F-08 Gerçek Zamanlı İzleme**
Web Socket aracılığıyla dolly kuyruğu ve yükleme durumu anlık olarak güncellenir.

**F-09 EOL Veri Entegrasyonu**
TrixServices bileşeni, EOL istasyon veritabanlarından dolly verilerini periyodik olarak çekerek merkezi sisteme aktarır.

**F-10 Denetim Günlüğü (Audit Log)**
Kritik tüm işlemler (giriş, dolly okutma, sevkiyat onayı, hata) kullanıcı ve zaman damgasıyla birlikte kayıt altına alınır.

### 2.3 Kullanıcı Sınıfları ve Özellikleri

| Kullanıcı Sınıfı | Erişim Kanalı | Teknik Yetkinlik | Temel Görevler |
|------------------|--------------|-----------------|---------------|
| **Web Admin** | Web Tarayıcı | Orta-İleri | Kullanıcı/rol yönetimi, sistem ayarları, log inceleme |
| **Web Operatör** | Web Tarayıcı | Temel-Orta | Sevkiyat onayı, dolly kuyruğu izleme, ASN/İrsaliye gönderimi |
| **Forklift Operatör** | Android El Terminali | Temel | Barkod ile giriş, dolly okutma, yükleme tamamlama |
| **Fabrika Yöneticisi** | Web Tarayıcı | Orta | Analitik raporlar, performans metrikleri, üretim takibi |
| **IT Yöneticisi** | Sunucu + Web | İleri | Sistem bakımı, servis yönetimi, güvenlik yapılandırması |
| **Sistem Entegratörü** | API | İleri | CEVA entegrasyonu, EOL servis yapılandırması |

### 2.4 Çalışma Ortamı

**Sunucu Ortamı:**

| Bileşen | Teknoloji | Versiyon |
|---------|-----------|---------|
| İşletim Sistemi (Backend) | Linux (Ubuntu/Debian) | 20.04+ |
| Web Sunucusu | Nginx | 1.18+ |
| WSGI Sunucusu | Gunicorn | 21.0+ |
| Backend Framework | Python / Flask | Python 3.9+, Flask 2.3 |
| Veritabanı | Microsoft SQL Server | 2019+ |
| ODBC Sürücüsü | ODBC Driver for SQL Server | 18 |

**İstemci Ortamı:**

| Bileşen | Teknoloji | Versiyon |
|---------|-----------|---------|
| Web Tarayıcı | Chrome, Edge, Firefox | Son 2 ana sürüm |
| Frontend Framework | React + Vite | React 18+, Vite 4+ |
| CSS Framework | Tailwind CSS | 3.x |
| Mobil İşletim Sistemi | Android | 8.0 (API 26)+ |
| Android Geliştirme | Java + Retrofit | Java 11+, Retrofit 2.x |
| EOL Servis OS | Windows | 10/Server 2016+ |

**Ağ Gereksinimleri:**

- Backend sunucusu ve SQL Server arasında kesintisiz LAN bağlantısı (10 Mbps minimum)
- Android cihazlar için fabrika Wi-Fi ağı (2.4/5 GHz)
- CEVA servisine HTTPS erişimi için internet bağlantısı (443/TCP)

### 2.5 Tasarım ve Uygulama Kısıtlamaları

**KS-01** Tüm backend API'leri RESTful mimaride tasarlanmış olmalı ve JSON formatında yanıt vermelidir.

**KS-02** Kimlik doğrulama JWT (JSON Web Token) standardını (RFC 7519) kullanmalıdır.

**KS-03** Veritabanı Microsoft SQL Server üzerinde çalışmalıdır; başka bir RDBMS sisteme dahil edilmemelidir.

**KS-04** Android uygulaması minimum API seviyesi 26 (Android 8.0) desteklemelidir.

**KS-05** CEVA entegrasyonu yalnızca mevcut SOAP web servis arayüzü üzerinden gerçekleştirilmelidir.

**KS-06** Tüm zaman damgaları Türkiye yerel saatinde (UTC+3) saklanmalı ve gösterilmelidir.

**KS-07** Şifreler veritabanında açık metin olarak saklanmamalı; bcrypt veya eşdeğer güçlü bir hash algoritmasıyla korunmalıdır.

**KS-08** Sistem yapılandırması `config/config.yaml` dosyasından yüklenmeli ve yeniden derleme gerektirmeden değiştirilebilir olmalıdır.

**KS-09** Kritik işlemler hata durumunda veritabanı işlemlerini geri almalı (rollback) ve hata kayıt altına alınmalıdır.

**KS-10** Tüm REST API endpointleri için standart HTTP durum kodları kullanılmalıdır (200, 201, 400, 401, 403, 404, 500).

### 2.6 Kullanıcı Dokümantasyonu

Aşağıdaki dokümantasyon bileşenleri temin edilmelidir:

| Belge | Hedef Kitle | Konu |
|-------|------------|------|
| Bu SRS Belgesi | Geliştiriciler, Yöneticiler | Gereksinim tanımı |
| Android API Rehberi | Android Geliştiriciler | API entegrasyon kılavuzu |
| Kurulum Rehberi | IT Yöneticileri | Sistem kurulumu ve konfigürasyonu |
| Operatör Kullanım Kılavuzu | Web Operatörleri | Günlük operasyon |
| Forklift Kullanım Kılavuzu | Forklift Operatörleri | El terminali kullanımı |
| Admin Paneli Rehberi | Web Adminleri | Kullanıcı ve sistem yönetimi |

### 2.7 Varsayımlar ve Bağımlılıklar

**Varsayımlar:**

- EOL istasyon sistemleri dolly verilerini SQL Server'a otomatik yazacaktır.
- Fabrika içi Wi-Fi ağı Android cihazlar için yeterli sinyal gücüne sahiptir.
- Kullanıcıların sisteme erişmek için gerekli cihazlara (bilgisayar/el terminali) sahip olduğu varsayılmaktadır.
- CEVA web servisinin UAT ve üretim ortamlarında erişilebilir olduğu kabul edilmektedir.

**Bağımlılıklar:**

- Microsoft SQL Server veritabanı erişimi zorunludur.
- CEVA SOAP web servisi ASN/İrsaliye gönderimi için gereklidir.
- Fabrika ağı (LAN/Wi-Fi) tüm bileşenler için altyapı sağlamalıdır.
- ODBC Driver 18 for SQL Server, backend sunucusuna kurulu olmalıdır.

---

## 3. Sistem Özellikleri ve Fonksiyonel Gereksinimler

Bu bölümdeki gereksinimler aşağıdaki öncelik skalasına göre sınıflandırılmıştır:

| Öncelik | Tanım |
|---------|-------|
| **ZORUNLU** | Sistemin temel işlevselliği için vazgeçilmezdir |
| **ÖNERİLEN** | Önemli değer katar; mümkün olduğunca uygulanmalıdır |
| **İSTEĞE BAĞLI** | Ekstra değer sağlar; kaynak durumuna göre değerlendirilebilir |

---

### 3.1 HarmonyEcoSystem — Control Tower Backend

#### 3.1.1 Kimlik Doğrulama ve Yetkilendirme

**SFR-AUTH-001** *(ZORUNLU)*
Sistem, web kullanıcıları için oturum tabanlı kimlik doğrulama sağlamalıdır.

- **Giriş:** Kullanıcı adı ve şifre
- **Çıkış:** Oturum kimlik bilgisi
- **Kural:** Hatalı giriş denemesi sayısı 5'i geçtiğinde hesap geçici olarak kilitlenmelidir.

**SFR-AUTH-002** *(ZORUNLU)*
Forklift operatörleri çalışan barkodu ile kimlik doğrulaması yapabilmelidir.

- **Giriş:** `operatorBarcode` (çalışan barkodu), `deviceId` (Android cihaz tanımlayıcısı)
- **Çıkış:** JWT oturum belirteci, operatör adı, son kullanma tarihi
- **Kural:** JWT belirteçleri 8 saat geçerlidir.
- **Kural:** Her operatör aynı anda yalnızca bir aktif oturuma sahip olabilir.

**SFR-AUTH-003** *(ZORUNLU)*
Sistem dört kullanıcı rolünü desteklemelidir: `admin`, `operator`, `terminal_admin`, `terminal_operator`.

**SFR-AUTH-004** *(ZORUNLU)*
JWT doğrulaması gerektiren tüm API endpointleri geçersiz veya süresi dolmuş belirteç için HTTP 401 döndürmelidir.

**SFR-AUTH-005** *(ZORUNLU)*
Forklift oturumu çıkış işlemi sırasında JWT belirteci geçersiz kılınmalıdır.

#### 3.1.2 Dolly Kuyruk Yönetimi

**SFR-QUEUE-001** *(ZORUNLU)*
Sistem, EOL istasyonlarından gelen tüm dolly'leri `DollyEOLInfo` tablosunda gerçek zamanlı olarak izlemelidir.

**SFR-QUEUE-002** *(ZORUNLU)*
Her dolly barkod okutma işlemi, mevcut bir yükleme oturumuna (loading session) bağlanmalıdır.

**SFR-QUEUE-003** *(ZORUNLU)*
Sistem dolly'leri grup ve EOL istasyonuna göre filtreleyebilmeli ve sıralayabilmelidir.

**SFR-QUEUE-004** *(ZORUNLU)*
Forklift operatörü yanlışlıkla okutulan son dolly'yi LIFO (Last In First Out) kuralıyla silebilmelidir.

- **Kural:** Yalnızca en son okutulan dolly kaldırılabilir.
- **Kural:** Kaldırma işlemi AuditLog'a kaydedilmelidir.

**SFR-QUEUE-005** *(ZORUNLU)*
Dolly kuyruğundan silinen kayıtlar `DollyQueueRemoved` tablosuna arşiv kaydı olarak eklenmelidir.

#### 3.1.3 Yükleme Oturumu Yönetimi

**SFR-LOAD-001** *(ZORUNLU)*
Her yükleme işlemi için benzersiz bir `LoadingSessionId` oluşturulmalıdır.

- **Format:** `LOAD_<YYYYMMDD>_<OperatorName>` (örn: `LOAD_20251126_MEHMET`)

**SFR-LOAD-002** *(ZORUNLU)*
Sistem bir yükleme oturumundaki dolly'lerin sırasını (`ScanOrder`) kaydetmelidir.

**SFR-LOAD-003** *(ZORUNLU)*
Forklift operatörü "Yükleme Tamamlandı" işlemini gerçekleştirdiğinde tüm `scanned` durumundaki kayıtlar `loading_completed` durumuna geçmelidir.

**SFR-LOAD-004** *(ÖNERİLEN)*
Sistem çoklu eş zamanlı yükleme oturumunu desteklemelidir (farklı operatörler aynı anda farklı yüklemeler yapabilmelidir).

#### 3.1.4 Sevkiyat Onayı

**SFR-SHIP-001** *(ZORUNLU)*
Web operatörü sefer numarası ve plaka bilgisini girerek sevkiyatı onaylayabilmelidir.

**SFR-SHIP-002** *(ZORUNLU)*
Sefer numarası aşağıdaki kurallara uygun olmalıdır:

- Format: `^[A-Z]{2,5}\d{4,10}$` veya `^[A-Z0-9]{5,20}$`
- Aynı sefer numarası birden fazla kullanılamaz.

**SFR-SHIP-003** *(ZORUNLU)*
Plaka numarası Türk trafik plaka formatına uygun olmalıdır.

- Format: `^\d{2}[A-Z]{1,3}\d{2,5}$` (örn: `34 ABC 123`)

**SFR-SHIP-004** *(ZORUNLU)*
Operatör kısmi sevkiyat yapabilmeli; bir yükleme oturumundaki dolly'lerin yalnızca bir bölümünü gönderebilmelidir.

**SFR-SHIP-005** *(ZORUNLU)*
Sevkiyat onayı tamamlandığında ilgili kayıtlar `DollySubmissionHold`'dan silinerek `SeferDollyEOL` tablosuna kalıcı olarak aktarılmalıdır.

**SFR-SHIP-006** *(ZORUNLU)*
Sistem gönderim türünü desteklemelidir: `asn` (ASN), `irsaliye` (İrsaliye), `both` (Her İkisi).

#### 3.1.5 CEVA Entegrasyonu

**SFR-CEVA-001** *(ZORUNLU)*
Sistem ASN gönderimi için CEVA DT Supplier SOAP web servisiyle entegre olmalıdır.

**SFR-CEVA-002** *(ZORUNLU)*
Sistem UAT ve üretim ortamlarını desteklemeli; ortam `config/config.yaml` üzerinden değiştirilebilmelidir.

**SFR-CEVA-003** *(ZORUNLU)*
CEVA servis çağrısı başarısız olduğunda sistem yeniden deneme mekanizması uygulamalıdır.

- **Kural:** Maksimum yeniden deneme sayısı yapılandırılabilir olmalıdır (varsayılan: 2).
- **Kural:** Başarısız CEVA çağrısı AuditLog'a kaydedilmelidir.

#### 3.1.6 Grup Yönetimi

**SFR-GROUP-001** *(ZORUNLU)*
Admin paneli EOL istasyonlarını mantıksal gruplara atayabilmelidir.

**SFR-GROUP-002** *(ZORUNLU)*
Her grup için gönderim etiketi tanımlanabilmelidir: ASN, İrsaliye veya Her İkisi.

**SFR-GROUP-003** *(ZORUNLU)*
Sistem `PWorkStation` tablosundan EOL istasyonlarını otomatik olarak tarayabilmeli; adı `EOL` ile biten istasyonları listelemelidir.

**SFR-GROUP-004** *(ÖNERİLEN)*
`pworkstation.require_finish_product_station` yapılandırması etkinleştirildiğinde yalnızca bitmiş ürün istasyonları listelenmeli.

#### 3.1.7 Denetim Günlüğü

**SFR-AUDIT-001** *(ZORUNLU)*
Aşağıdaki işlemler `AuditLog` tablosuna kaydedilmelidir:

- Forklift oturum açma/kapama
- Dolly barkod okutma
- Dolly kaldırma (LIFO)
- Yükleme tamamlama
- Sevkiyat onayı
- Kritik sistem hataları

**SFR-AUDIT-002** *(ZORUNLU)*
Her denetim kaydı şu alanları içermelidir: işlem türü, aktör (kullanıcı/sistem), kaynak, zaman damgası, JSON metadata.

**SFR-AUDIT-003** *(ZORUNLU)*
Uygulama günlükleri döngüsel dosya rotasyonu ile `logs/app.log` dosyasına yazılmalıdır.

#### 3.1.8 Dolly Yaşam Döngüsü İzleme

**SFR-LC-001** *(ZORUNLU)*
Her dolly'nin durum geçişleri `DollyLifecycle` tablosuna kaydedilmelidir.

**SFR-LC-002** *(ZORUNLU)*
Aşağıdaki durumlar tanımlı olmalıdır:

| Durum | Tetikleyen Olay |
|-------|----------------|
| `EOL_READY` | Dolly EOL'den çıkar |
| `SCAN_CAPTURED` | Forklift barkod okutma |
| `LOADING_IN_PROGRESS` | Yükleme devam ediyor |
| `LOADING_COMPLETED` | Yükleme tamamlandı |
| `WAITING_OPERATOR` | Operatör onayı bekleniyor |
| `COMPLETED_ASN` | ASN gönderimi tamamlandı |
| `COMPLETED_IRS` | İrsaliye gönderimi tamamlandı |
| `COMPLETED_BOTH` | ASN ve İrsaliye tamamlandı |

#### 3.1.9 Analitik Modül

**SFR-ANALYTICS-001** *(ÖNERİLEN)*
Sistem, veritabanı view'leri aracılığıyla aşağıdaki metrikleri sunmalıdır:

- Üretimden taramaya geçen ortalama süre
- Taramadan yükleme tamamlamaya geçen ortalama süre
- Yüklemeden sevkiyata geçen ortalama süre
- Operatör başına işlenen dolly sayısı
- Vardiya bazlı üretim ve sevkiyat hacmi

**SFR-ANALYTICS-002** *(ÖNERİLEN)*
Analitik veriler salt okunur SQL view'ları üzerinden sorgulanmalı; doğrudan tablo erişiminden kaçınılmalıdır.

**SFR-ANALYTICS-003** *(İSTEĞE BAĞLI)*
Sistem, Excel formatında rapor dışa aktarma özelliği sunabilir.

---

### 3.2 HarmonyEcoSystemTrixServices — Windows EOL Servisleri

**SFR-TRIX-001** *(ZORUNLU)*
Servis, EOL istasyon veritabanlarından dolly verilerini periyodik aralıklarla çekmelidir.

**SFR-TRIX-002** *(ZORUNLU)*
Servis bir Windows Background Service olarak kurulabilmeli ve `install_service.bat` / `uninstall_service.bat` betiklerle yönetilebilmelidir.

**SFR-TRIX-003** *(ZORUNLU)*
Servis, sistem yeniden başlamasında otomatik olarak başlamalıdır.

**SFR-TRIX-004** *(ZORUNLU)*
Tüm servis yapılandırması `config.json` dosyasından okunmalıdır:

- EOL veritabanı bağlantı bilgileri
- Merkezi SQL Server bağlantı bilgileri
- Sorgulama aralığı
- Günlük dosya yolu

**SFR-TRIX-005** *(ZORUNLU)*
Servis, aktarım sırasında oluşan hatalar için yeniden deneme mekanizması içermelidir.

**SFR-TRIX-006** *(ZORUNLU)*
Servis kendi çalışma günlüğünü dosya bazlı loglama ile tutmalıdır.

---

### 3.3 HarmonyMobileApp — Android El Terminali

#### 3.3.1 Kimlik Doğrulama

**SFR-MOB-AUTH-001** *(ZORUNLU)*
Uygulama açıldığında kayıtlı JWT belirteci yoksa giriş ekranı gösterilmelidir.

**SFR-MOB-AUTH-002** *(ZORUNLU)*
Giriş ekranı barkod okuyucu veya manuel giriş ile çalışan barkodunu kabul etmelidir.

**SFR-MOB-AUTH-003** *(ZORUNLU)*
Başarılı girişte JWT belirteci cihazda güvenli biçimde saklanmalı (`SharedPreferences`) ve sonraki tüm API isteklerinde kullanılmalıdır.

**SFR-MOB-AUTH-004** *(ZORUNLU)*
HTTP 401 yanıtı alındığında uygulama belirteci temizlemeli ve kullanıcıyı otomatik olarak giriş ekranına yönlendirmelidir.

#### 3.3.2 Dolly Tarama

**SFR-MOB-SCAN-001** *(ZORUNLU)*
Operatör dolly barkodunu okutarak aktif yükleme oturumuna ekleyebilmelidir.

**SFR-MOB-SCAN-002** *(ZORUNLU)*
Her başarılı taramadan sonra ekranda sıra numarası ve dolly numarası gösterilmelidir.

**SFR-MOB-SCAN-003** *(ZORUNLU)*
Aynı dolly aynı yükleme oturumunda ikinci kez okutulamaz; sistem uyarı vermelidir.

**SFR-MOB-SCAN-004** *(ZORUNLU)*
Operatör LIFO kuralıyla son okutulan dolly'yi kaldırabilmelidir.

#### 3.3.3 Yükleme Tamamlama

**SFR-MOB-COMP-001** *(ZORUNLU)*
"Yükleme Tamamlandı" butonu basıldığında oturumdaki tüm dolly'ler `loading_completed` durumuna geçirilmelidir.

**SFR-MOB-COMP-002** *(ZORUNLU)*
İşlem başarılı olduğunda ekranda yüklenen dolly sayısı ve tamamlanma zamanı gösterilmelidir.

#### 3.3.4 Kiosk Modu

**SFR-MOB-KIOSK-001** *(ZORUNLU)*
Uygulama kiosk modunda çalışacak şekilde yapılandırılabilmelidir.

**SFR-MOB-KIOSK-002** *(ZORUNLU)*
Kiosk modunda kullanıcı uygulamadan çıkamaz veya başka uygulamalara geçemez.

#### 3.3.5 Hata Yönetimi

**SFR-MOB-ERR-001** *(ZORUNLU)*
Tüm API hatalarında kullanıcıya anlaşılır Türkçe mesaj gösterilmelidir.

**SFR-MOB-ERR-002** *(ZORUNLU)*
`retryable: true` olan hatalar için yeniden deneme seçeneği sunulmalıdır.

**SFR-MOB-ERR-003** *(ZORUNLU)*
Ağ bağlantısı kesildiğinde uygulama çalışmaya devam etmeli ve kullanıcıyı bilgilendirmelidir.

---

### 3.4 HarmonyView — Yönetici ve Operatör Dashboard'ları

#### 3.4.1 Operatör Paneli

**SFR-VIEW-OP-001** *(ZORUNLU)*
Operatör paneli, yükleme tamamlandı durumundaki yükleme oturumlarını listelemeli ve sevkiyat detaylarını göstermelidir.

**SFR-VIEW-OP-002** *(ZORUNLU)*
Operatör, bir yükleme oturumundaki dolly'leri seçerek (checkbox) kısmi sevkiyat gerçekleştirebilmelidir.

**SFR-VIEW-OP-003** *(ZORUNLU)*
Sevkiyat formunda sefer numarası, plaka ve gönderim türü seçimi yer almalıdır.

**SFR-VIEW-OP-004** *(ÖNERİLEN)*
Panel, Web Socket bağlantısı aracılığıyla yeni yükleme oturumlarını gerçek zamanlı olarak göstermelidir.

#### 3.4.2 Yönetici Dashboard'u

**SFR-VIEW-MAN-001** *(ZORUNLU)*
Yönetici dashboard'u üretim ve sevkiyat özetini günlük, haftalık ve aylık bazda sunmalıdır.

**SFR-VIEW-MAN-002** *(ÖNERİLEN)*
Dashboard, üretim hattından sevkiyata kadar tüm süreç aşamalarının gecikme analizini göstermelidir.

**SFR-VIEW-MAN-003** *(İSTEĞE BAĞLI)*
Dashboard, natural language (doğal dil) ile veri sorgulama yapabilen chatbot arayüzü içerebilir.

#### 3.4.3 TV/Büyük Ekran Modu

**SFR-VIEW-TV-001** *(ÖNERİLEN)*
Sistem, fabrika içi bilgi ekranları için optimize edilmiş ayrı bir TV görünümü sunabilmelidir.

**SFR-VIEW-TV-002** *(ÖNERİLEN)*
TV modu otomatik yenileme özelliğine sahip olmalıdır (30 sn aralıklarla).

#### 3.4.4 Admin Paneli

**SFR-VIEW-ADM-001** *(ZORUNLU)*
Admin paneli kullanıcı oluşturma, silme ve şifre sıfırlama işlemlerini desteklemelidir.

**SFR-VIEW-ADM-002** *(ZORUNLU)*
Admin paneli terminal cihazı kayıt ve yönetim özelliğini içermelidir.

**SFR-VIEW-ADM-003** *(ZORUNLU)*
Admin paneli sistem günlüklerini (dosya günlüğü + AuditLog) görüntüleyebilmelidir.

---

## 4. Dış Arayüz Gereksinimleri

### 4.1 Kullanıcı Arayüzleri

**AI-UI-001**
Web arayüzleri Türkçe dil desteğiyle geliştirilmelidir.

**AI-UI-002**
Web Dashboard'lar duyarlı tasarıma (responsive design) sahip olmalı; minimum 1280×720 çözünürlükte sorunsuz çalışmalıdır.

**AI-UI-003**
Android uygulaması Material Design ilkelerine uygun olarak geliştirilmelidir.

**AI-UI-004**
Tüm hata mesajları kullanıcıya anlaşılır, teknik olmayan dilde sunulmalıdır.

**AI-UI-005**
Web formları istemci taraflı doğrulama (validation) içermelidir.

### 4.2 Donanım Arayüzleri

**AI-HW-001**
Android uygulaması, Honeywell veya Zebra markalı endüstriyel el terminalleri dahil olmak üzere entegre barkod okuyuculu Android cihazlarda çalışmalıdır.

**AI-HW-002**
Sistem, fiziksel USB veya Bluetooth barkod okuyuculardan gelen giriş verilerini işleyebilmelidir.

**AI-HW-003**
Sunucu bileşeni minimum 4 GB RAM ve 2 CPU çekirdeğine sahip donanımda çalışabilmelidir.

### 4.3 Yazılım Arayüzleri

**AI-SW-001** — CEVA SOAP Web Service

| Alan | Değer |
|------|-------|
| Protokol | HTTPS (TLS 1.2+) |
| Format | SOAP/XML |
| UAT URL | https://trtmsuat.cevalogistics.com/Ceva.DT.Supplier.WebService/ |
| Üretim URL | https://trweb04.cevalogistics.com/Ceva.DT.Supplier.WebService/ |
| Kimlik Doğrulama | Tedarikçi kodu + kullanıcı adı/şifre |
| Zaman Aşımı | 30 saniye |

**AI-SW-002** — SQL Server

| Alan | Değer |
|------|-------|
| Driver | ODBC Driver 18 for SQL Server |
| Şifreleme | `Encrypt=yes` |
| Sertifika Doğrulama | `TrustServerCertificate=yes` (yapılandırılabilir) |
| Bağlantı Havuzu | SQLAlchemy bağlantı havuzu |

**AI-SW-003** — Android REST API

| Alan | Değer |
|------|-------|
| HTTP İstemcisi | Retrofit 2.x |
| JSON Serileştirme | Gson |
| Kimlik Doğrulama | Bearer Token (JWT) |
| Timeout | Bağlantı: 30 sn, Okuma: 60 sn |

### 4.4 İletişim Arayüzleri

**AI-COM-001**
Backend API HTTP (8181/TCP) ve HTTPS (443/TCP) protokolleri üzerinden hizmet vermelidir.

**AI-COM-002**
Gerçek zamanlı güncellemeler için WebSocket bağlantısı kullanılmalıdır (Flask-SocketIO / Socket.IO).

**AI-COM-003**
Tüm üretim ortamı API iletişimi TLS 1.2 veya üzeri ile şifrelenmelidir.

**AI-COM-004**
Android uygulaması, bağlantı kesildiğinde otomatik yeniden bağlanma mekanizması içermelidir.

---

## 5. Fonksiyonel Olmayan Gereksinimler

### 5.1 Performans Gereksinimleri

**NFR-PERF-001**
API endpointleri normal yük altında 1 saniye içinde yanıt vermelidir.

**NFR-PERF-002**
Dolly listesi sorguları 10.000 aktif kayıt içinde 2 saniyeyi geçmemelidir.

**NFR-PERF-003**
Sistem aynı anda en az 50 eş zamanlı kullanıcıyı performans kaybı olmaksızın desteklemelidir.

**NFR-PERF-004**
Web dashboard sayfaları ilk yüklemede 3 saniyenin altında açılmalıdır (LAN bağlantısı ile).

**NFR-PERF-005**
Analitik view sorguları 5 saniye içinde tamamlanmalıdır.

### 5.2 Güvenlik Gereksinimleri

**NFR-SEC-001**
Tüm kullanıcı şifreleri bcrypt veya Argon2 ile hashlenmiş biçimde saklanmalıdır.

**NFR-SEC-002**
JWT belirteçleri güvenli rastgele anahtar ile imzalanmalı; anahtar `config/config.yaml` içindeki `secret_key` alanı üzerinden yönetilmelidir.

**NFR-SEC-003**
Üretim ortamında tüm HTTP trafiği HTTPS üzerinden yönlendirilmelidir.

**NFR-SEC-004**
SQL enjeksiyonuna karşı tüm veritabanı sorguları parametreli (ORM) kullanılmalıdır.

**NFR-SEC-005**
Web formları Cross-Site Request Forgery (CSRF) korumasına sahip olmalıdır.

**NFR-SEC-006**
Admin paneli yalnızca `admin` rolündeki kullanıcılar tarafından erişilebilir olmalıdır.

**NFR-SEC-007**
Yapılandırma dosyalarındaki şifreler ve API anahtarları sürüm kontrol sistemine dahil edilmemelidir.

**NFR-SEC-008**
Hatalı giriş girişimleri sistematik olarak AuditLog'a kaydedilmelidir.

### 5.3 Güvenilirlik ve Erişilebilirlik

**NFR-REL-001**
Sistem, planlı bakımlar dışında %99 veya üzeri çalışma süresi (uptime) hedefini karşılamalıdır.

**NFR-REL-002**
Sistem, Python uygulama hatalarından otomatik olarak kurtarılabilmeli; `systemd` servisi kilitlenme durumunda uygulamayı yeniden başlatmalıdır.

**NFR-REL-003**
Veritabanı işlemleri hata durumunda tam geri alma (rollback) ile tutarlı duruma dönmelidir.

**NFR-REL-004**
CEVA servis erişiminin geçici olarak kesilmesi durumunda sistem çalışmaya devam etmeli; CEVA bağımlı işlemler yeniden deneme kuyruğuna alınmalıdır.

**NFR-REL-005**
Günlük uygulama yedeklemesi kritik veritabanı tablolarını kapsamalıdır.

### 5.4 Sürdürülebilirlik

**NFR-MAINT-001**
Tüm API endpointleri, veri modelleri ve iş kuralları bu SRS belgesiyle belgelenmelidir.

**NFR-MAINT-002**
Veritabanı şema değişiklikleri numara sıralı SQL migration betikleri (`database/XXX_*.sql`) aracılığıyla yönetilmelidir.

**NFR-MAINT-003**
Uygulama yapılandırması tek bir YAML dosyasında (`config/config.yaml`) merkezi olarak yönetilmelidir.

**NFR-MAINT-004**
Backend kodunun modüler yapısı korunmalıdır: `routes/`, `services/`, `models/`, `utils/` katmanları birbirinden bağımsız olmalıdır.

**NFR-MAINT-005**
Yeni servis veya özellik eklemek için mevcut kod değiştirilmeden Flask Blueprint mimarisine uygun ekleme yapılabilmelidir.

### 5.5 Taşınabilirlik

**NFR-PORT-001**
Backend uygulaması Linux ve Windows Server ortamlarında değişiklik gerektirmeden çalışabilmelidir.

**NFR-PORT-002**
Android uygulaması, manifest ile talep edilen izinler dışında cihaza özgü API kullanmaktan kaçınmalıdır.

**NFR-PORT-003**
Veritabanı migration betikleri standart T-SQL söz diziminde yazılmalı ve SQL Server 2019+ ile uyumlu olmalıdır.

---

## 6. Veritabanı Gereksinimleri

### 6.1 Veri Modeli

Sistem aşağıdaki ana tabloları kullanmaktadır:

#### Birincil İş Tabloları

| Tablo | Birincil Anahtar | Amaç |
|-------|-----------------|------|
| `DollyEOLInfo` | `DollyNo` + `VinNo` (Bileşik) | EOL'den gelen canlı dolly kuyruğu |
| `DollySubmissionHold` | `Id` (INT AUTO) | Forklift tarafından okutulan geçici kayıtlar |
| `SeferDollyEOL` | `Id` (INT AUTO) | Tamamlanmış sevkiyat kalıcı arşivi |
| `DollyLifecycle` | `Id` (INT AUTO) | Dolly durum geçiş günlüğü |
| `DollyQueueRemoved` | `Id` (INT AUTO) | Kuyruktan kaldırılan dolly arşivi |

#### Grup Yönetimi Tabloları

| Tablo | Amaç |
|-------|------|
| `DollyGroup` | Mantıksal dolly grupları |
| `DollyGroupEOL` | Grup–EOL ilişkilendirmesi ve gönderim etiketi |
| `PWorkStation` | Üretim istasyonları (EOL dahil) |

#### Kimlik Doğrulama ve Güvenlik Tabloları

| Tablo | Amaç |
|-------|------|
| `UserRole` | Kullanıcı rol tanımları |
| `UserAccount` | Kullanıcı hesapları (web) |
| `TerminalDevice` | Kayıtlı terminal cihazları |
| `ForkliftLoginSession` | Forklift JWT oturum kayıtları |
| `TerminalBarcodeSession` | Tek kullanımlık barkod OTP oturumları |

#### İzleme ve Denetim Tabloları

| Tablo | Amaç |
|-------|------|
| `AuditLog` | Kritik işlem denetim günlüğü |
| `WebOperatorTask` | Web operatör görev kuyruğu |

### 6.2 Veri Bütünlüğü

**NFR-DB-001**
`DollyEOLInfo` tablosuna `DollyNo + VinNo` çifti için bileşik birincil anahtar kısıtlaması uygulanmalıdır.

**NFR-DB-002**
`ForkliftLoginSession.SessionToken` alanı UNIQUE kısıtlamasına sahip olmalıdır.

**NFR-DB-003**
`DollySubmissionHold.Status` alanı yalnızca tanımlı değerleri kabul etmelidir: `pending`, `scanned`, `loading_completed`, `completed`, `removed`.

**NFR-DB-004**
`SeferDollyEOL` tablosuna yazılan kayıtlar silinmemeli; tarihsel veri bütünlüğü korunmalıdır.

**NFR-DB-005**
Tüm tarih/zaman alanları `DATETIME2` veri tipiyle tanımlanmalıdır.

### 6.3 Veri Saklama ve Arşivleme

**NFR-DB-SA-001**
Dolly yaşam döngüsü kayıtları (`DollyLifecycle`) silinmemeli; sonraki analitik sorgular için saklanmalıdır.

**NFR-DB-SA-002**
`AuditLog` kayıtları en az 1 yıl süreyle saklanmalıdır.

**NFR-DB-SA-003**
`DollySubmissionHold` tablosu periyodik temizleme politikasına tabi tutulabilir; ancak temizleme öncesinde kayıtlar arşivlenmelidir.

---

## 7. Sistem Kısıtlamaları

**SK-001 Ağ Bağımlılığı**
Sistem çevrimiçi çalışmaktadır; ağ bağlantısının kesilmesi durumunda işlevsellik kısıtlanır. Çevrimdışı çalışma bu kapsamın dışındadır.

**SK-002 Veritabanı Tekeli**
Sistem yalnızca Microsoft SQL Server ile uyumludur. Başka bir RDBMS sistemi için ek geliştirme gereklidir.

**SK-003 CEVA Bağımlılığı**
ASN ve İrsaliye işlemleri CEVA Logistics hizmet sağlayıcısına bağımlıdır. CEVA sistem kesintileri bu özelliklerin çalışmamasına neden olur.

**SK-004 Android Sürüm Kısıtlaması**
Android uygulaması minimum Android 8.0 (API 26) gerektirir. Eski cihazlar desteklenmez.

**SK-005 Yerelleştirme**
Sistem Türkçe dil desteğiyle geliştirilmiştir. Çoklu dil desteği bu sürümün kapsamı dışındadır.

**SK-006 Tek Kiracı Mimari**
Mevcut mimari tek kiracı (single-tenant) kullanım için tasarlanmıştır. Çok kiracılı yapı ek geliştirme gerektirir.

**SK-007 EOL Sistemi Bağımlılığı**
`DollyEOLInfo` verisi EOL üretim sisteminden gelmektedir. EOL sisteminin çalışmaması durumunda yeni dolly verisi sisteme girmez.

---

## 8. İzlenebilirlik Matrisi

Aşağıdaki matris, gereksinimleri sistem bileşenleri ve uygulama dosyalarıyla ilişkilendirir:

| Gereksinim ID | Açıklama | Bileşen | Uygulama Dosyası |
|---------------|----------|---------|-----------------|
| SFR-AUTH-001 | Web oturum doğrulama | EcoSystem | `app/routes/auth.py` |
| SFR-AUTH-002 | Forklift barkod girişi | EcoSystem | `app/utils/forklift_auth.py` |
| SFR-AUTH-003 | Rol tabanlı erişim kontrolü | EcoSystem | `app/models/user.py` |
| SFR-AUTH-004 | JWT doğrulama | EcoSystem | `app/utils/forklift_auth.py` |
| SFR-AUTH-005 | Oturum kapatma | EcoSystem | `app/routes/api.py` |
| SFR-QUEUE-001 | Dolly kuyruğu izleme | EcoSystem | `app/models/dolly.py` |
| SFR-QUEUE-002 | Yükleme oturumu yönetimi | EcoSystem | `app/services/dolly_service.py` |
| SFR-QUEUE-003 | Grup ve EOL filtresi | EcoSystem | `app/routes/api.py` |
| SFR-QUEUE-004 | LIFO dolly kaldırma | EcoSystem | `app/services/dolly_service.py` |
| SFR-QUEUE-005 | Kaldırılan dolly arşivi | EcoSystem | `app/models/dolly_queue_removed.py` |
| SFR-LOAD-001 | LoadingSessionId oluşturma | EcoSystem | `app/services/dolly_service.py` |
| SFR-LOAD-002 | Tarama sırası kaydı | EcoSystem | `app/models/dolly_backup.py` |
| SFR-SHIP-001 | Sevkiyat onayı | EcoSystem | `app/services/dolly_service.py` |
| SFR-SHIP-002 | Sefer numarası doğrulama | EcoSystem | `app/services/dolly_service.py` |
| SFR-SHIP-003 | Plaka doğrulama | EcoSystem | `app/services/dolly_service.py` |
| SFR-SHIP-004 | Kısmi sevkiyat | EcoSystem | `app/services/dolly_service.py` |
| SFR-SHIP-005 | SeferDollyEOL aktarımı | EcoSystem | `app/services/dolly_service.py` |
| SFR-CEVA-001 | CEVA SOAP entegrasyonu | EcoSystem | `app/services/ceva_service.py` |
| SFR-CEVA-002 | UAT/Üretim ortam seçimi | EcoSystem | `config/config.yaml` |
| SFR-GROUP-001 | EOL grup ataması | EcoSystem | `app/models/group.py` |
| SFR-AUDIT-001 | Denetim kaydı | EcoSystem | `app/services/audit_service.py` |
| SFR-LC-001 | Yaşam döngüsü izleme | EcoSystem | `app/services/lifecycle_service.py` |
| SFR-TRIX-001 | EOL veri çekme | TrixServices | `DollyEOLService/dolly_service.py` |
| SFR-TRIX-002 | Windows Servis kurulumu | TrixServices | `install_service.bat` |
| SFR-TRIX-004 | Servis yapılandırması | TrixServices | `config.json` |
| SFR-MOB-AUTH-001 | Giriş ekranı | MobileApp | `LoginActivity.java` |
| SFR-MOB-SCAN-001 | Dolly tarama | MobileApp | `app/src/main/java/…/ScanActivity.java` |
| SFR-MOB-COMP-001 | Yükleme tamamlama | MobileApp | `app/src/main/java/…/GroupActivity.java` |
| SFR-MOB-KIOSK-001 | Kiosk modu | MobileApp | `setup_kiosk.sh` |
| SFR-VIEW-OP-001 | Operatör sevkiyat listesi | HarmonyView | `backend/app.py` |
| SFR-VIEW-MAN-001 | Yönetici dashboard | HarmonyView | `frontend-manager/src/App.jsx` |
| SFR-VIEW-ADM-001 | Kullanıcı yönetimi | EcoSystem | `app/routes/dashboard.py` |
| NFR-SEC-001 | Şifre hashleme | EcoSystem | `app/utils/security.py` |
| NFR-DB-001 | Bileşik PK kısıtlaması | DB | `database/001_*.sql` |
| NFR-DB-004 | Tarihsel veri koruma | DB | `app/models/sefer.py` |

---

## 9. Ekler

### Ek A — API Referansı

#### A.1 Kimlik Doğrulama Endpoint'leri

**POST /api/forklift/login**

| Alan | Detay |
|------|-------|
| Kimlik Doğrulama | Gerekmez |
| İstek Gövdesi | `{ "operatorBarcode": "EMP123", "deviceId": "android-001" }` |
| Başarılı Yanıt (200) | `{ "success": true, "sessionToken": "eyJ...", "operatorName": "Ad Soyad", "expiresAt": "2025-11-27T08:00:00Z" }` |
| Hata Yanıtı (401) | `{ "error": "Geçersiz barkod", "retryable": true }` |

**POST /api/forklift/logout**

| Alan | Detay |
|------|-------|
| Kimlik Doğrulama | Bearer Token (JWT) |
| İstek Gövdesi | Boş |
| Başarılı Yanıt (200) | `{ "success": true, "message": "Çıkış yapıldı" }` |

**GET /api/forklift/session/validate**

| Alan | Detay |
|------|-------|
| Kimlik Doğrulama | Bearer Token (JWT) |
| Başarılı Yanıt (200) | `{ "valid": true, "operatorName": "Ad Soyad", "expiresAt": "2025-11-27T08:00:00Z" }` |

#### A.2 Forklift Operasyon Endpoint'leri

**POST /api/forklift/scan**

| Alan | Detay |
|------|-------|
| Kimlik Doğrulama | Bearer Token (JWT) |
| İstek Gövdesi | `{ "dollyNo": "DL-5170427", "loadingSessionId": "LOAD_20251126_MEHMET", "barcode": "BARCODE123" }` |
| Başarılı Yanıt (200) | `{ "dolly_no": "DL-5170427", "vin_no": "VIN001", "scan_order": 1, "loading_session_id": "LOAD_..." }` |
| Hata (409) | Dolly zaten okutulmuş |
| Hata (404) | Dolly bulunamadı |

**POST /api/forklift/complete-loading**

| Alan | Detay |
|------|-------|
| Kimlik Doğrulama | Bearer Token (JWT) |
| İstek Gövdesi | `{ "loadingSessionId": "LOAD_20251126_MEHMET" }` |
| Başarılı Yanıt (200) | `{ "loadingSessionId": "LOAD_...", "dollyCount": 15, "completedAt": "2025-11-26T10:30:00Z" }` |

**POST /api/forklift/remove-last**

| Alan | Detay |
|------|-------|
| Kimlik Doğrulama | Bearer Token (JWT) |
| İstek Gövdesi | `{ "loadingSessionId": "LOAD_...", "dollyBarcode": "BARCODE123" }` |
| Başarılı Yanıt (200) | `{ "dollyNo": "DL-5170427", "scanOrder": 15, "removedAt": "2025-11-26T10:30:00Z" }` |
| Hata (400) | Sadece en son dolly kaldırılabilir |

**GET /api/forklift/sessions**

| Alan | Detay |
|------|-------|
| Kimlik Doğrulama | Bearer Token (JWT) |
| Sorgu Parametresi | `status`: `scanned`, `loading_completed`, `completed` (isteğe bağlı) |
| Başarılı Yanıt (200) | `[{ "loadingSessionId": "...", "dollyCount": 8, "status": "loading_completed", ... }]` |

#### A.3 Web Operatör Endpoint'leri

**GET /api/operator/pending-shipments**

| Alan | Detay |
|------|-------|
| Kimlik Doğrulama | Web oturumu |
| Başarılı Yanıt (200) | `[{ "loadingSessionId": "...", "dollyCount": 15, "operatorName": "...", "completedAt": "..." }]` |

**POST /api/operator/complete-shipment**

| Alan | Detay |
|------|-------|
| Kimlik Doğrulama | Web oturumu |
| İstek Gövdesi | `{ "loadingSessionId": "...", "seferNumarasi": "SFR20250001", "plakaNo": "34 ABC 123", "shippingType": "both", "selectedDollyIds": [1, 2, 4] }` |
| Başarılı Yanıt (200) | `{ "loadingSessionId": "...", "dollyCount": 3, "partialShipment": true, "completedAt": "..." }` |
| Hata (400) | Geçersiz sefer/plaka formatı veya mükerrer sefer |

#### A.4 Yardımcı Endpoint'ler

| Endpoint | Metod | Kimlik Doğrulama | Açıklama |
|----------|-------|-----------------|----------|
| `/api/health` | GET | Gerekmez | Sunucu sağlık durumu |
| `/api/groups` | GET | Gerekmez | Tüm dolly grupları |
| `/api/group-sequences` | GET | Gerekmez | EOL bazlı grup sıralamaları |
| `/api/pworkstations/eol` | GET | Gerekmez | EOL istasyonlarını listele |
| `/api/groups/definitions` | GET | Gerekmez | Grup tanımları |
| `/api/manual-collection/groups` | GET | Bearer Token | Manuel toplama grup listesi |

#### A.5 Hata Yanıt Formatı

Tüm API hata yanıtları aşağıdaki standart formatı kullanır:

```json
{
  "error": "Kullanıcıya gösterilecek mesaj (Türkçe)",
  "message": "Teknik detay",
  "retryable": true
}
```

| HTTP Kodu | Tür | `retryable` | Açıklama |
|-----------|-----|-------------|----------|
| 400 | Doğrulama Hatası | `true` | Kullanıcı girişi düzeltebilir |
| 401 | Kimlik Doğrulama Hatası | `false` | Giriş ekranına yönlendir |
| 403 | Yetkilendirme Hatası | `false` | Yetkisiz erişim |
| 404 | Kaynak Bulunamadı | `false` | Kaynak mevcut değil |
| 409 | Çakışma | `true` | Mükerrer kayıt |
| 500 | Sistem Hatası | `true` | Rollback + yeniden dene |

---

### Ek B — Veritabanı Şeması

#### B.1 DollyEOLInfo

```sql
-- Ana kuyruk tablosu — EOL'den gelen dolly'ler
CREATE TABLE DollyEOLInfo (
    DollyNo          NVARCHAR(50)  NOT NULL,
    VinNo            NVARCHAR(50)  NOT NULL,
    DollyOrderNo     NVARCHAR(50)  NULL,
    CustomerReferans NVARCHAR(100) NULL,
    Adet             INT           NULL,
    EOLName          NVARCHAR(100) NULL,
    EOLID            INT           NULL,
    EOLDATE          DATE          NULL,
    EOLDollyBarcode  NVARCHAR(100) NULL,
    RECEIPTID        NVARCHAR(50)  NULL,
    InsertedAt       DATETIME2     DEFAULT GETDATE(),
    CONSTRAINT PK_DollyEOLInfo PRIMARY KEY (DollyNo, VinNo)
);
```

#### B.2 DollySubmissionHold

```sql
-- Forklift tarafından okutulan geçici kayıtlar
CREATE TABLE DollySubmissionHold (
    Id                   INT           PRIMARY KEY IDENTITY(1,1),
    DollyNo              NVARCHAR(50)  NOT NULL,
    VinNo                NVARCHAR(50)  NOT NULL,
    Status               NVARCHAR(30)  NOT NULL DEFAULT 'pending',
    TerminalUser         NVARCHAR(100) NULL,
    ScanOrder            INT           NULL,
    LoadingSessionId     NVARCHAR(50)  NULL,
    LoadingCompletedAt   DATETIME2     NULL,
    SeferNumarasi        NVARCHAR(20)  NULL,
    PlakaNo              NVARCHAR(20)  NULL,
    PartNumber           NVARCHAR(50)  NULL,
    EOLName              NVARCHAR(100) NULL,
    EOLID                INT           NULL,
    CustomerReferans     NVARCHAR(100) NULL,
    Adet                 INT           NULL,
    SubmittedAt          DATETIME2     NULL,
    InsertedAt           DATETIME2     DEFAULT GETDATE()
);
```

#### B.3 ForkliftLoginSession

```sql
-- Forklift JWT oturum kayıtları
CREATE TABLE ForkliftLoginSession (
    Id               INT            PRIMARY KEY IDENTITY(1,1),
    OperatorBarcode  NVARCHAR(50)   NOT NULL,
    OperatorName     NVARCHAR(100)  NULL,
    SessionToken     NVARCHAR(128)  UNIQUE NOT NULL,
    IsActive         BIT            DEFAULT 1,
    LoginAt          DATETIME2      DEFAULT GETDATE(),
    ExpiresAt        DATETIME2      NOT NULL,
    LastActivityAt   DATETIME2      NULL,
    DeviceId         NVARCHAR(100)  NULL,
    LogoutAt         DATETIME2      NULL,
    Role             NVARCHAR(30)   DEFAULT 'terminal_operator'
);
```

#### B.4 AuditLog

```sql
-- Denetim günlüğü
CREATE TABLE AuditLog (
    Id          INT            PRIMARY KEY IDENTITY(1,1),
    Action      NVARCHAR(100)  NOT NULL,
    ActorType   NVARCHAR(50)   NULL,
    ActorName   NVARCHAR(100)  NULL,
    Resource    NVARCHAR(100)  NULL,
    Metadata    NVARCHAR(MAX)  NULL,
    CreatedAt   DATETIME2      DEFAULT GETDATE()
);
```

#### B.5 SeferDollyEOL

```sql
-- Tamamlanmış sevkiyat kalıcı arşivi
CREATE TABLE SeferDollyEOL (
    Id                INT            PRIMARY KEY IDENTITY(1,1),
    DollyNo           NVARCHAR(50)   NOT NULL,
    VinNo             NVARCHAR(50)   NOT NULL,
    SeferNumarasi     NVARCHAR(20)   NOT NULL,
    PlakaNo           NVARCHAR(20)   NOT NULL,
    EOLName           NVARCHAR(100)  NULL,
    EOLID             INT            NULL,
    DollyOrderNo      NVARCHAR(50)   NULL,
    PartNumber        NVARCHAR(50)   NULL,
    CustomerReferans  NVARCHAR(100)  NULL,
    ScanOrder         INT            NULL,
    LoadingSessionId  NVARCHAR(50)   NULL,
    ShippingType      NVARCHAR(20)   NULL,
    Lokasyon          NVARCHAR(100)  NULL,
    SubmittedAt       DATETIME2      DEFAULT GETDATE(),
    InsertedAt        DATETIME2      NULL
);
```

#### B.6 DollyLifecycle

```sql
-- Dolly durum geçiş günlüğü
CREATE TABLE DollyLifecycle (
    Id           INT            PRIMARY KEY IDENTITY(1,1),
    DollyNo      NVARCHAR(50)   NOT NULL,
    VinNo        NVARCHAR(50)   NOT NULL,
    Status       NVARCHAR(50)   NOT NULL,
    Actor        NVARCHAR(100)  NULL,
    SessionId    NVARCHAR(50)   NULL,
    Notes        NVARCHAR(500)  NULL,
    CreatedAt    DATETIME2      DEFAULT GETDATE()
);
```

---

### Ek C — Sözlük

| Terim | Türkçe Açıklama |
|-------|----------------|
| **Audit Log** | Sistemdeki kritik işlemlerin kim tarafından, ne zaman yapıldığını kaydeden denetim günlüğü |
| **Bearer Token** | HTTP Authorization başlığında taşınan JWT kimlik doğrulama belirteci |
| **CEVA** | Magna'nın ASN ve İrsaliye işlemlerini yönettiği lojistik hizmet sağlayıcısı |
| **Control Tower** | Dolly lojistiğini izleyen ve koordine eden merkezi kontrol sistemi |
| **Dolly** | Üretim hattında parça taşımak için kullanılan tekerlekli taşıma arabası |
| **EOL (End of Line)** | Üretim hattının son noktası; dolly'lerin üretimden çıkarak sisteme girdiği nokta |
| **Forklift Operatörü** | TIR yükleme işlemini gerçekleştiren ve Android el terminali kullanan çalışan |
| **GSDB** | Ford Motor Company Global Supplier Database — tedarikçi tanımlama sistemi |
| **Gunicorn** | Python WSGI uygulamalarını production ortamında çalıştırmak için kullanılan HTTP sunucu |
| **İrsaliye** | Türk mevzuatına göre malların taşınması sırasında taşınan resmi belge |
| **JIT (Just-In-Time)** | Parçaların tam ihtiyaç duyulduğunda teslim edilmesine dayanan üretim yöntemi |
| **JWT** | Kullanıcı kimliğini ve yetki bilgilerini taşıyan imzalanmış JSON formatındaki belirteç |
| **Kiosk Modu** | Kullanıcının yalnızca belirli bir uygulamayı kullanmasına izin veren kilitli cihaz modu |
| **LIFO** | Last In First Out — Sisteme en son eklenen öğenin ilk çıkarılması kuralı |
| **Loading Session** | Bir forklift operatörünün tek bir TIR için oluşturduğu yükleme oturumu |
| **Migration** | Veritabanı şemasında yapılan değişiklikleri sıralı SQL betikleri aracılığıyla uygulama süreci |
| **Nginx** | Flask uygulaması önünde çalışan yüksek performanslı web/ters proxy sunucusu |
| **Operatör (Web)** | Sevkiyat onayı yapan, ASN/İrsaliye gönderen web paneli kullanıcısı |
| **Rollback** | Hata durumunda veritabanı işlemlerinin önceki tutarlı duruma geri alınması |
| **SeferDollyEOL** | Tamamlanmış sevkiyat işlemlerinin kalıcı olarak saklandığı arşiv tablosu |
| **Sefer Numarası** | Web operatörünün girdiği benzersiz sevkiyat tanımlayıcısı |
| **Socket.IO** | Gerçek zamanlı iki yönlü iletişim sağlayan WebSocket kütüphanesi |
| **SOAP** | Simple Object Access Protocol — CEVA entegrasyonunda kullanılan XML tabanlı web servis protokolü |
| **systemd** | Linux'ta sistem servisleri yönetmek için kullanılan init sistemi ve servis yöneticisi |
| **TIR** | Transport International Routier — Avrupa ve uluslararası karayolu taşımacılığında kullanılan araç |
| **VIN** | Vehicle Identification Number — Her araca özgü şasi/araç kimlik numarası |
| **WSGI** | Web Server Gateway Interface — Python web uygulamaları için standart sunucu arayüzü |

---

*Bu belge ISO/IEC/IEEE 29148:2018 standardına uygun olarak hazırlanmıştır.*

*Belge No: MAGNA-TR-SRS-001 | Versiyon: 1.0.0 | Magna IT Türkiye Ekibi | 2026-02-21*
