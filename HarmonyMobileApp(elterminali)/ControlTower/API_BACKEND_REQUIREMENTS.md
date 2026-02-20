# 🔧 Backend API Gereksinimleri - Android Uygulama Entegrasyonu

**Tarih:** 23 Aralık 2025  
**Versiyon:** 1.1.0  
**Backend Ekibi İçin**

---

## 📋 İçindekiler

1. [Admin Login Desteği](#1-admin-login-desteği)
2. [VIN Format Doğrulaması](#2-vin-format-doğrulaması)
3. [Smart Refresh Optimizasyonu](#3-smart-refresh-optimizasyonu)
4. [Veritabanı Değişiklikleri](#4-veritabanı-değişiklikleri)

---

## 1. Admin Login Desteği

### 🎯 Amaç
Admin kullanıcıları barkod ile giriş yaptığında, uygulama Admin Panel'e yönlendirilmeli.

### ✅ Gereksinimler

#### API Endpoint
```http
POST /api/forklift/login
Content-Type: application/json
```

#### Request (Değişiklik Yok)
```json
{
  "operatorBarcode": "ADMIN001",
  "deviceId": "android-serial-123456"
}
```

#### Response - Normal Kullanıcı
```json
{
  "success": true,
  "sessionToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "operatorName": "Mehmet Yılmaz",
  "operatorBarcode": "EMP12345",
  "expiresAt": "2025-12-23T16:00:00Z",
  "message": "Hoş geldiniz Mehmet Yılmaz",
  "isAdmin": false,
  "role": "forklift"
}
```

#### Response - Admin Kullanıcı (YENİ)
```json
{
  "success": true,
  "sessionToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "operatorName": "Admin User",
  "operatorBarcode": "ADMIN001",
  "expiresAt": "2025-12-23T16:00:00Z",
  "message": "Hoş geldiniz Admin User",
  "isAdmin": true,
  "role": "admin"
}
```

### 📝 Yeni Alanlar

| Alan | Tip | Zorunlu | Açıklama |
|------|-----|---------|----------|
| `isAdmin` | Boolean | ✅ Evet | Kullanıcının admin olup olmadığını belirtir |
| `role` | String | ✅ Evet | Kullanıcı rolü: "admin", "forklift", "operator" vb. |

### 💡 Backend İşlem Akışı

```javascript
// Pseudocode
async function login(operatorBarcode) {
  // 1. Veritabanından kullanıcıyı bul
  const user = await db.findUserByBarcode(operatorBarcode);
  
  if (!user) {
    return { success: false, message: "Kullanıcı bulunamadı" };
  }
  
  // 2. Session token oluştur
  const sessionToken = generateJWT(user);
  
  // 3. Response hazırla
  return {
    success: true,
    sessionToken: sessionToken,
    operatorName: user.name,
    operatorBarcode: user.barcode,
    expiresAt: new Date(Date.now() + 8 * 60 * 60 * 1000), // 8 saat
    message: `Hoş geldiniz ${user.name}`,
    isAdmin: user.is_admin || false,  // ⭐ YENİ ALAN
    role: user.role || 'forklift'      // ⭐ YENİ ALAN
  };
}
```

---

## 2. VIN Format Doğrulaması

### 🎯 Amaç
Dolly'lerdeki VIN'lerin doğru formatta gönderildiğinden emin olunmalı.

### ✅ Mevcut Format (Değişiklik Yok)

#### API Endpoint
```http
GET /api/manual-collection/groups/{groupName}
Authorization: Bearer <sessionToken>
```

#### Response Format
```json
{
  "group_name": "V710-MR-EOL",
  "dollys": [
    {
      "dolly_no": "5170427",
      "vin_no": "VIN001\nVIN002\nVIN003",
      "scanned": false
    },
    {
      "dolly_no": "5170428",
      "vin_no": "VIN004\nVIN005",
      "scanned": true
    }
  ]
}
```

### ⚠️ Önemli Notlar

1. **VIN Ayırıcı:** VIN'ler `\n` (newline) karakteri ile ayrılmalı
2. **Format:** Her VIN ayrı satırda
3. **Boşluklar:** VIN'lerin başında/sonunda boşluk olmamalı
4. **Encoding:** UTF-8
5. **Login Endpoint:** `/login` endpoint'i **Authorization header gerektirmez** - token almak için kullanılır

#### ✅ Doğru Örnekler:
```
"VIN001\nVIN002\nVIN003"
"VIN001"
"68200089\n68200090\n68200091"
```

#### ❌ Yanlış Örnekler:
```
"VIN001,VIN002,VIN003"  // Virgül kullanılmış
"VIN001 VIN002 VIN003"  // Boşluk kullanılmış
"VIN001;VIN002;VIN003"  // Noktalı virgül kullanılmış
```

### 💡 Backend Validation

```javascript
// VIN formatı doğrulama
function formatVinList(vinArray) {
  // VIN dizisini \n ile birleştir
  return vinArray.join('\n');
}

// Örnek:
const vins = ['VIN001', 'VIN002', 'VIN003'];
const vinString = formatVinList(vins);
// Sonuç: "VIN001\nVIN002\nVIN003"
```

---

## 3. Smart Refresh Optimizasyonu

### 🎯 Amaç
Uygulama her 1 saniyede bir API'yi çağırıyor. Veri değişmediyse response hızlı olmalı.

### ✅ Gereksinimler

#### Etkilenen Endpoint'ler

1. **Grup Listesi**
   ```http
   GET /api/manual-collection/groups
   Authorization: Bearer <sessionToken>
   ```

2. **Grup Detayı**
   ```http
   GET /api/manual-collection/groups/{groupName}
   Authorization: Bearer <sessionToken>
   ```

### 📊 Performance Beklentileri

| Senaryo | Beklenen Süre | Açıklama |
|---------|---------------|----------|
| Veri değişmemiş | < 50ms | Cache'den dön |
| Veri değişmiş | < 200ms | DB'den fresh data |
| Network timeout | 5000ms | Timeout süresi |

### 💡 Backend Optimizasyon Önerileri

#### 1. Redis Cache Kullanımı
```javascript
async function getManualCollectionGroups(sessionToken) {
  const cacheKey = 'manual_collection_groups';
  
  // Cache kontrol et
  let cachedData = await redis.get(cacheKey);
  if (cachedData) {
    return JSON.parse(cachedData);
  }
  
  // DB'den çek
  const groups = await db.getEOLGroups();
  
  // Cache'e kaydet (1 saniye TTL)
  await redis.set(cacheKey, JSON.stringify(groups), 'EX', 1);
  
  return groups;
}
```

#### 2. Conditional Request (ETag)
```http
Request:
GET /api/manual-collection/groups
If-None-Match: "abc123xyz"

Response (Veri değişmemişse):
HTTP/1.1 304 Not Modified
ETag: "abc123xyz"

Response (Veri değişmişse):
HTTP/1.1 200 OK
ETag: "def456uvw"
{
  "groups": [...]
}
```

### ⚠️ Kritik Notlar

- Android uygulama **her 1 saniyede** API çağırıyor
- Backend'in bu yükü kaldırabilmesi gerekiyor
- Cache stratejisi önemli
- Veri değişmediyse hızlı response şart

---

## 4. Veritabanı Değişiklikleri

### 🗄️ Operators Tablosu

#### Mevcut Yapı
```sql
CREATE TABLE Operators (
  operator_id INT PRIMARY KEY,
  operator_barcode VARCHAR(50) UNIQUE,
  operator_name VARCHAR(100),
  created_at DATETIME,
  updated_at DATETIME
);
```

#### Yeni Yapı
```sql
ALTER TABLE Operators 
ADD COLUMN is_admin BOOLEAN DEFAULT 0;

ALTER TABLE Operators 
ADD COLUMN role VARCHAR(20) DEFAULT 'forklift';

-- Index ekle (performance için)
CREATE INDEX idx_operators_role ON Operators(role);
```

#### Admin Kullanıcıları İşaretle
```sql
-- Admin kullanıcıları güncelle
UPDATE Operators 
SET is_admin = 1, role = 'admin' 
WHERE operator_barcode IN ('ADMIN001', 'ADMIN002', 'ADMIN123');

-- Doğrulama
SELECT operator_barcode, operator_name, is_admin, role 
FROM Operators 
WHERE is_admin = 1;
```

### 📋 Role Tipleri

| Role | Açıklama | Yetki Seviyesi |
|------|----------|----------------|
| `admin` | Sistem yöneticisi | Tüm yetkiler + ayarlar |
| `forklift` | Forklift operatörü | Dolly yükleme/tarama |
| `operator` | Genel operatör | Okuma yetkisi |
| `viewer` | İzleyici | Sadece görüntüleme |

---

## 5. Test Senaryoları

### ✅ Test Case 1: Admin Login
```bash
curl -X POST http://10.25.1.174:8181/api/forklift/login \
  -H "Content-Type: application/json" \
  -d '{
    "operatorBarcode": "ADMIN001",
    "deviceId": "test-device"
  }'

# Beklenen Response:
{
  "success": true,
  "sessionToken": "...",
  "operatorName": "Admin User",
  "isAdmin": true,
  "role": "admin"
}
```

### ✅ Test Case 2: Normal User Login
```bash
curl -X POST http://10.25.1.174:8181/api/forklift/login \
  -H "Content-Type: application/json" \
  -d '{
    "operatorBarcode": "EMP12345",
    "deviceId": "test-device"
  }'

# Beklenen Response:
{
  "success": true,
  "sessionToken": "...",
  "operatorName": "Mehmet Yılmaz",
  "isAdmin": false,
  "role": "forklift"
}
```

### ✅ Test Case 3: VIN Format
```bash
curl -X GET http://10.25.1.174:8181/api/manual-collection/groups/V710-MR-EOL \
  -H "Authorization: Bearer <token>"

# Beklenen Response:
{
  "group_name": "V710-MR-EOL",
  "dollys": [
    {
      "dolly_no": "5170427",
      "vin_no": "VIN001\nVIN002\nVIN003",  // ⭐ \n ile ayrılmış
      "scanned": false
    }
  ]
}
```

### ✅ Test Case 4: Smart Refresh Performance
```bash
# 10 kez arka arkaya çağır
for i in {1..10}; do
  time curl -X GET http://10.25.1.174:8181/api/manual-collection/groups \
    -H "Authorization: Bearer <token>" \
    -s -o /dev/null -w "Request $i: %{time_total}s\n"
done

# Beklenen: Ortalama < 100ms
```

---

## 6. Hata Yönetimi

### ❌ Admin Login - Kullanıcı Bulunamadı
```json
{
  "success": false,
  "message": "Operatör barkodu tanınmıyor"
}
```

### ❌ Invalid Token
```json
HTTP/1.1 401 Unauthorized
{
  "error": "Token geçersiz veya süresi dolmuş"
}
```

### ❌ VIN Format Hatası
```json
{
  "error": "VIN formatı hatalı. VIN'ler \\n ile ayrılmalı"
}
```

---

## 7. Migration Checklist

Backend ekibinin tamamlaması gereken adımlar:

### Phase 1: Database (Kritik)
- [ ] `Operators` tablosuna `is_admin` kolonu ekle
- [ ] `Operators` tablosuna `role` kolonu ekle
- [ ] Index'leri oluştur
- [ ] Admin kullanıcıları işaretle
- [ ] Test dataları ekle

### Phase 2: API Response (Kritik)
- [ ] Login endpoint'ine `isAdmin` alanı ekle
- [ ] Login endpoint'ine `role` alanı ekle
- [ ] Backward compatibility kontrolü
- [ ] Unit test yaz

### Phase 3: Performance (Yüksek Öncelik)
- [ ] Redis cache implementasyonu
- [ ] ETag desteği ekle (opsiyonel)
- [ ] Load testing yap (1 req/sec)
- [ ] Response time monitoring

### Phase 4: VIN Format (Doğrulama)
- [ ] VIN format kontrolü
- [ ] `\n` ayırıcı doğrulaması
- [ ] Boşluk temizleme
- [ ] Validation test

### Phase 5: Testing
- [ ] Admin login test
- [ ] Normal user login test
- [ ] VIN format test
- [ ] Performance test
- [ ] Integration test

---

## 8. Deployment Plan

### 🚀 Rollout Stratejı

#### Aşama 1: Development (Hemen)
- Database migration çalıştır
- API değişikliklerini deploy et
- Test et

#### Aşama 2: Staging (1 gün sonra)
- Full integration test
- Performance test
- Android app test

#### Aşama 3: Production (2-3 gün sonra)
- Prod migration
- Monitoring aktif
- Rollback planı hazır

---

## 9. Rollback Planı

### ⚠️ Sorun Durumunda

```sql
-- Database rollback
ALTER TABLE Operators DROP COLUMN is_admin;
ALTER TABLE Operators DROP COLUMN role;

-- API rollback
-- Eski version'a dön
git revert <commit-hash>
```

---

## 10. İletişim

### 📞 Sorular veya Sorunlar İçin:

- **Android Ekip:** [İsim/Email]
- **Backend Ekip:** [İsim/Email]
- **Slack Kanal:** #control-tower-dev

---

## 11. Referanslar

- [ANDROID_COMPLETE_INTEGRATION_GUIDE.md](./docs/ANDROID_COMPLETE_INTEGRATION_GUIDE.md)
- [ANDROID_QUICK_REFERENCE_GUIDE.md](./docs/ANDROID_QUICK_REFERENCE_GUIDE.md)
- [RELEASE_NOTES.md](./RELEASE_NOTES.md)

---

## ✅ Özet

### En Kritik Değişiklikler:

1. **Login Response'a 2 yeni alan:**
   - `isAdmin` (Boolean)
   - `role` (String)

2. **VIN Format Doğrulaması:**
   - `\n` karakteri ile ayrılmış olmalı

3. **Performance:**
   - 1 req/sec yükü kaldırmalı
   - Cache stratejisi öneriliyor

4. **Database:**
   - `Operators` tablosuna 2 kolon ekle
   - Admin kullanıcıları işaretle

---

**Son Güncelleme:** 23 Aralık 2025  
**Versiyon:** 1.0  
**Status:** 🟡 Pending Implementation
