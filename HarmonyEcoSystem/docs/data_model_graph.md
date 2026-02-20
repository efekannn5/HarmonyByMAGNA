## HarmonyEcoSystem – Veri Modeli ve Gelecek Adımlar

## HarmonyEcoSystem – Teknik Veri Modeli ve Bağlantı Analizi

### 🔗 Tablo İlişkileri ve Foreign Key Yapısı

#### **Foreign Key Bağlantıları:**
```sql
-- Grup Yönetimi
DollyGroupEOL.GroupId → DollyGroup.Id
DollyGroupEOL.PWorkStationId → PWorkStation.Id

-- Kullanıcı Yönetimi  
UserAccount.RoleId → UserRole.Id
TerminalDevice.RoleId → UserRole.Id
TerminalBarcodeSession.DeviceId → TerminalDevice.Id
TerminalBarcodeSession.UserId → UserAccount.Id
```

#### **Logical İlişkiler (FK olmayan bağlantılar):**
```sql
-- Dolly Takip Zinciri
DollyEOLInfo.DollyNo ≈ DollyLifecycle.DollyNo
DollyEOLInfo.DollyNo ≈ DollySubmissionHold.DollyNo  
DollySubmissionHold.DollyNo ≈ SeferDollyEOL.DollyNo

-- EOL İstasyon Eşleştirme
DollyEOLInfo.EOLName ≈ PWorkStation.PWorkStationName
```

### 🗃️ Detaylı Tablo Açıklamaları
- **AuditLog** – Her kritik işlem için actor, aksiyon, kaynak ve metadata saklar. Hem SQL üzerinden sorgulanır hem de dosya loguna yansıtılır.
- **DollyEOLInfo** – EOL hattından gelen canlı dolly/VIN eşleşmeleri; müşteri referansı, adet, EOL kimliği ve isteğe bağlı barkod (`EOLDollyBarcode`) alanını içerir.
- **DollyGroup** – Operasyonel kural kümeleri: aynı sevkiyata gidecek EOL istasyonlarını tek çatı altında toplar.
- **DollyGroupEOL** – Bir grubun hangi `PWorkStation` kayıtlarını içerdiğini ve bu istasyonlarda hangi gönderim etiketi (ASN/İrsaliye/Both) uygulanacağını tanımlar.
- **DollyLifecycle** – Dollynin yaşam döngüsü (EOL_READY, SCAN_CAPTURED, WAITING_SUBMIT, SUBMITTED_TERMINAL, WAITING_OPERATOR, COMPLETED_[*]) kaydını tutar; tarihçe raporları için ana kaynak.
- **DollySubmissionHold** – Forklift okutması ile terminal onayı arasındaki bekleyen kayıtlar; barcode/terminal kullanıcı bilgisi burada tutulur.
- **PWorkStation** – Tesisin tüm iş istasyonlarını içerir. `EOL` ile biten isimler EOL olarak kabul edilip gruplar için aday listesi olur.
- **SeferDollyEOL** – Operatör onayı sonrası gönderim kayıtları; ASN/İrsaliye tarihleri shipping etiketine göre doldurulur, lojistik geçmiş burada saklanır.
- **TerminalBarcodeSession** – Terminal kullanıcılarının barkod/OTP oturumları; token, bitiş zamanı ve kullanıldığı zaman.
- **TerminalDevice** – Kullanıcıya bağlı terminal konfigürasyonu ve cihaz anahtarları; barkod üretimi için gizli anahtarlar burada tutulur.
- **UserAccount** – Web ve terminal kullanıcı kayıtları; bcrypt/argon2 hash’li şifreler, rol, aktif/pasif durumu, son giriş.
- **UserRole** – Rol tanımları (admin, operator, terminal_admin, terminal_operator); izin setleri uygulamada bu tablodan türetilir.

### Mermaid Graph (graph TB) - Gelişmiş Teknik Diyagram
```mermaid
graph TB
    subgraph "🏭 PRODUCTION LAYER"
        DEI[("🚗 DollyEOLInfo<br/>📊 Canlı Üretim<br/>🔑 DollyNo")]
        PWS[("⚙️ PWorkStation<br/>🏗️ İstasyon Master<br/>🔑 Id")]
    end
    
    subgraph "🚛 OPERATIONAL LAYER"  
        DLC[("📈 DollyLifecycle<br/>⏱️ Durum Takibi<br/>🔄 Status History")]
        DSH[("⏳ DollySubmissionHold<br/>🔄 Geçici Queue<br/>📱 Terminal Bridge")]
        DG[("📦 DollyGroup<br/>🏷️ Mantıksal Gruplar<br/>🔑 Id")]
        DGE[("🔗 DollyGroupEOL<br/>⚡ Group↔Station<br/>📋 ShippingTag")]
    end
    
    subgraph "📦 SHIPMENT LAYER"
        SDE[("🚚 SeferDollyEOL<br/>📋 Sevkiyat Geçmiş<br/>📅 ASN/İrsaliye")]
    end
    
    subgraph "👥 SECURITY LAYER"
        UR[("🛡️ UserRole<br/>⚡ admin/operator<br/>terminal_admin/operator")]
        UA[("👤 UserAccount<br/>🔐 bcrypt Hash<br/>🎯 Role Based")]
        TD[("📱 TerminalDevice<br/>🔑 API Keys<br/>📟 Mobile Config")]
        TBS[("🎫 TerminalBarcodeSession<br/>⏰ OTP Tokens<br/>🔒 Temporary Access")]
    end
    
    subgraph "🔍 AUDIT LAYER"
        AL[("📋 AuditLog<br/>👀 Who→What→When<br/>🔍 Full Traceability")]
    end
    
    %% PRODUCTION CONNECTIONS
    DEI -.->|"dolly_no"| DLC
    DEI -.->|"dolly_no"| DSH
    PWS -->|"FK: PWorkStationId"| DGE
    
    %% OPERATIONAL CONNECTIONS  
    DG -->|"FK: GroupId"| DGE
    DSH -.->|"dolly_no"| SDE
    DGE -.->|"shipping_tag"| SDE
    
    %% SECURITY CONNECTIONS
    UR -->|"FK: RoleId"| UA
    UR -->|"FK: RoleId"| TD  
    TD -->|"FK: DeviceId"| TBS
    UA -->|"FK: UserId"| TBS
    
    %% AUDIT CONNECTIONS
    UA -.->|"actor"| AL
    TD -.->|"actor"| AL
    DLC -.->|"lifecycle_events"| AL
    DSH -.->|"terminal_actions"| AL
    SDE -.->|"shipment_events"| AL
    
    %% STYLING
    classDef production fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#1b5e20
    classDef operational fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#0d47a1
    classDef shipment fill:#fff3e0,stroke:#f57c00,stroke-width:3px,color:#e65100
    classDef security fill:#fce4ec,stroke:#c2185b,stroke-width:3px,color:#880e4f
    classDef audit fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#4a148c
    
    class DEI,PWS production
    class DLC,DSH,DG,DGE operational
    class SDE shipment  
    class UR,UA,TD,TBS security
    class AL audit
```

### 🔄 Veri Akış Süreçleri ve Bağlantı Detayları

#### **1. Dolly Yaşam Döngüsü Akışı**
```
📊 DollyEOLInfo (Üretim) 
    ↓ (dolly_no eşleştirme)
📈 DollyLifecycle (EOL_READY)
    ↓ (forklift barkod okutma)  
⏳ DollySubmissionHold (SCAN_CAPTURED)
    ↓ (terminal submit)
📈 DollyLifecycle (SUBMITTED_TERMINAL)
    ↓ (operatör web onayı)
🚚 SeferDollyEOL (sevkiyat kaydı)
    ↓
📈 DollyLifecycle (COMPLETED_*)
```

#### **2. Güvenlik ve Yetkilendirme Akışı**
```
🛡️ UserRole (rol tanımı)
    ↓ (FK: RoleId)
👤 UserAccount (kullanıcı)
    ↓ (terminal kullanıcı ise)
📱 TerminalDevice (cihaz yapılandırması) 
    ↓ (barkod giriş)
🎫 TerminalBarcodeSession (OTP token)
    ↓ (tüm aksiyonlar)
📋 AuditLog (izleme)
```

#### **3. Grup Yönetimi ve EOL İstasyon Akışı**
```
⚙️ PWorkStation (istasyon master)
    ↓ (adı 'EOL' ile bitenler)
📦 DollyGroup (grup oluşturma)
    ↓ (grup-istasyon eşleştirme)
🔗 DollyGroupEOL (ASN/İrsaliye etiket)
    ↓ (sevkiyat tag'i belirleme)
🚚 SeferDollyEOL (etiket bazlı tarih update)
```

### 📊 Kritik İş Kuralları ve Mantığı

#### **Barkod Doğrulama Kuralı:**
- `DollyEOLInfo.EOLDollyBarcode` ≠ NULL ise forklift okutma sırasında eşleştirme zorunlu
- Barkod eşleşmezse `DollySubmissionHold` kaydı reddedilir
- Audit log'a `barcode_mismatch` eventi düşer

#### **Sevkiyat Etiket Kuralı:**
- `DollyGroupEOL.ShippingTag` = "ASN" → sadece `SeferDollyEOL.ASNDate` doldurulur
- `DollyGroupEOL.ShippingTag` = "İrsaliye" → sadece `SeferDollyEOL.IrsaliyeDate` doldurulur  
- `DollyGroupEOL.ShippingTag` = "Both" → her iki tarih de doldurulur

#### **Lifecycle Durum Kontrolü:**
- Bir dolly `COMPLETED_*` durumuna geçtikten sonra tekrar işleme alınamaz
- Her durum değişikliği `AuditLog` tablosuna yansıtılır
- `WAITING_OPERATOR` durumundaki kayıtlar web dashboard'da görünür

#### **Terminal Güvenlik Kuralı:**
- `TerminalBarcodeSession.ExpiresAt` kontrol edilir (varsayılan 60 dakika)
- `UsedAt` dolduktan sonra token tekrar kullanılamaz
- Her API çağrısında `TerminalDevice.ApiKey` doğrulanır

1. **AuditLog** – `DollyLifecycle`, `UserAccount`, `TerminalDevice` gibi aktörlerden gelen tüm aksiyonları kaydeder; hem SQL’de hem dosyada bulunur.
2. **DollyEOLInfo ➜ DollyLifecycle** – EOL’den gelen her kayıt `EOL_READY` olarak lifecycle’a yansır; barkod eşleştirmesi bu tablodan yapılır.
3. **DollyEOLInfo ➜ DollySubmissionHold** – Forklift okutması gerçekleştiğinde `SCAN_CAPTURED` ve `WAITING_SUBMIT` durumları üretilir, barkod doğrulaması yapılır.
4. **DollySubmissionHold ➜ SeferDollyEOL** – Terminal `submit`, operator `ack` akışı tamamlandığında gönderim tarihçesi oluşur.
5. **DollyGroup ➜ DollyGroupEOL ➜ PWorkStation** – EOL istasyonları gruplara bağlanır; shipping tag (ASN/İrsaliye) operatör onayı sırasında hangi tarih alanının dolacağını belirler.
6. **SeferDollyEOL** – `DollyGroupEOL`’den gelen shipping tag’e göre ASNDate/IrsaliyeDate güncellenir; completed lifecycle finalize edilir.
7. **UserRole ➜ UserAccount ➜ TerminalDevice ➜ TerminalBarcodeSession** – Rol tabanlı yetkilendirme, kullanıcı hesapları, terminal cihaz yapılandırmaları ve barkod oturumları.
8. **AuditLog** – Kullanıcı oluşturma, barkod üretme, EOL grubu düzenleme, forklift okutma gibi kritik aksiyonlar buraya düşer.

### Gelecekte Eklenecek Planlanan Tablolar
| Tablo / Bileşen | Amaç |
|-----------------|------|
| `NotificationRule` | Belirli lifecycle durumlarında e-posta/SMS uyarıları tetiklemek. |
| `ShiftSchedule` | Hangi vardiyada hangi terminal kullanıcılarının aktif olduğu ve üretim planı eşleştirmesi. |
| `AnalyticsSnapshot` | Günlük/haftalık dolly throughput verilerini saklamak (dashboard grafikleri için). |
| `DeviceHealthLog` | Terminal cihazlarındaki hataları (batarya, bağlantı, barkod okuyucu arızası) izlemek. |
| `WebhookSubscription` | Harici sistemlere (SAP, MES vb.) tamamlanan gönderim bildirimlerini göndermek. |

Bu planlanan tablolar sayesinde ileride üretim analitiği, bildirim yönetimi ve cihaz sağlığı izleme konularında genişleme yapılabilecek. Şu anki yapı bu genişlemelere uygun şekilde modülerdir.
