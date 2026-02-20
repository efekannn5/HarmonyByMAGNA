# Control Tower - Release Notes

## Version 1.3.0 - 13 Ocak 2026

### 🎯 Yeni Özellikler

#### 1. Multi-EOL Group Submit Sistemi
- ✅ **Grup bazlı submit** - Birden fazla EOL içeren gruplarda topluca submit
- Tüm EOL'lerden taranan dolly'ler tek seferde submit edilebiliyor
- Submit dialogunda EOL bazında özet gösterimi:
  ```
  📊 Grup Özeti
  📍 V710-FR-EOL: 15 / 120 dolly
  📍 V710-LLS-EOL: 8 / 95 dolly
  📍 V710-MR-EOL: 23 / 150 dolly
  
  Toplam: 46 / 365 dolly tarandı
  ```
- Backend part number otomatik alınıyor
- API Endpoint: `POST /api/manual-collection/mobile-submit` (group_id, group_name, part_number)

#### 2. Grup Endpoint Entegrasyonu
- ✅ `GET /api/manual-collection/groups/{groupId}` endpoint entegrasyonu
- Tüm EOL'lerdeki dolly'lerin tek çağrıda alınması
- Nested JSON yapısı desteği:
  ```json
  {
    "group_id": 3,
    "group_name": "deneme1213",
    "part_number": "1070949",
    "eols": [
      {
        "eol_id": 1,
        "eol_name": "V710-FR-EOL",
        "dollys": [...]
      }
    ]
  }
  ```

#### 3. Backend Field Tutarsızlığı Düzeltmesi
- ✅ Hem `scanned` hem `is_scanned` field desteği
- Gson alternate annotation kullanımı
- Tek EOL endpoint: `scanned`
- Grup endpoint: `is_scanned`
- Her iki durumda da sorunsuz çalışıyor

#### 4. Akıllı Submit Butonu Kontrolü
- ✅ Submit butonu **grup bazında** aktif/pasif oluyor
- Herhangi bir EOL'de dolly tarandığında submit aktif
- Remove butonu **EOL bazında** aktif/pasif oluyor
- `totalGroupScannedCount` global değişkeni ile grup geneli takip

### 🔧 İyileştirmeler

#### 1. GroupDollysResponse Model Güncellemesi
- ✅ Nested EOL yapısı desteği
- Inner class: `EolGroup` (eol_id, eol_name, dollys)
- Daha temiz ve organize veri yapısı

#### 2. ManualSubmitRequest Güncellemesi
- ✅ `group_name` field eklendi (backend gereksinimi)
- Dual constructor desteği:
  - EOL bazlı: `ManualSubmitRequest(String eolName)`
  - Grup bazlı: `ManualSubmitRequest(Integer groupId, String groupName, String partNumber)`

#### 3. Auto Group Scanned Count Update
- ✅ `updateGroupScannedCount()` fonksiyonu
- Her dolly scan'den sonra otomatik güncelleme
- Activity başlangıcında initial load
- Submit butonunun doğru çalışması için real-time tracking

#### 4. Debug Logging İyileştirmesi
- ✅ Detaylı API response logging
- EOL bazında dolly sayısı logları
- Scanned dolly tracking logları
- Total scanned/total dollys gösterimi

### 🐛 Düzeltilen Hatalar

#### 1. Submit Butonu Görünmeme Sorunu
- ❌ **SORUN:** Başka EOL'de dolly taranmış olsa bile mevcut EOL'de tarama yoksa submit görünmüyordu
- ✅ **ÇÖZÜM:** Grup bazlı kontrol ile herhangi bir EOL'de tarama varsa submit aktif

#### 2. Backend Field Uyumsuzluğu
- ❌ **SORUN:** Tek EOL endpoint `scanned`, grup endpoint `is_scanned` gönderiyor
- ✅ **ÇÖZÜM:** Gson alternate annotation ile her iki field destekleniyor

#### 3. Submit Request Eksik Field
- ❌ **SORUN:** Backend `group_name` field'ı bekliyor ama kod göndermiyor
- ✅ **ÇÖZÜM:** ManualSubmitRequest'e `group_name` field'ı eklendi

#### 4. Okutulan Dolly'ler Yeşil Görünmüyor
- ❌ **SORUN:** Backend field adı uyumsuzluğu yüzünden `scanned` flag okunmuyor
- ✅ **ÇÖZÜM:** Alternate field name desteği ile sorun çözüldü

### 📋 API Değişiklikleri

#### Yeni Model Yapısı
```java
// GroupDollysResponse.java
public class GroupDollysResponse {
    private Integer groupId;
    private String groupName;
    private String partNumber;
    private List<EolGroup> eols;
    
    public static class EolGroup {
        private Integer eolId;
        private String eolName;
        private List<GroupDolly> dollys;
    }
}

// GroupDolly.java
public class GroupDolly {
    @SerializedName("dolly_no")
    private String dollyNo;
    
    @SerializedName(value = "is_scanned", alternate = {"scanned"})
    private boolean scanned;  // Her iki field adını destekler
}

// ManualSubmitRequest.java
public class ManualSubmitRequest {
    @SerializedName("group_id")
    private Integer groupId;
    
    @SerializedName("group_name")  // YENİ
    private String groupName;
    
    @SerializedName("part_number")
    private String partNumber;
}
```

#### Güncellenen Endpoints
```http
# Grup bazlı submit
POST /api/manual-collection/mobile-submit
Authorization: Bearer <token>
Content-Type: application/json

Request:
{
  "group_id": 3,
  "group_name": "deneme1213",
  "part_number": "1070949"
}

Response:
{
  "success": true,
  "message": "Grup başarıyla submit edildi",
  "submitted_count": 46,
  "vin_count": 368,
  "part_number": "1070949"
}

# Grup dolly listesi
GET /api/manual-collection/groups/{groupId}
Authorization: Bearer <token>

Response:
{
  "group_id": 3,
  "group_name": "deneme1213",
  "part_number": "1070949",
  "eols": [
    {
      "eol_id": 1,
      "eol_name": "V710-FR-EOL",
      "dollys": [
        {
          "dolly_no": "1071092",
          "dolly_order_no": "32012",
          "vin_no": "VIN1\\nVIN2\\nVIN3",
          "is_scanned": true
        }
      ]
    }
  ]
}
```

### 🔍 Test Senaryoları

#### Multi-EOL Submit Testi
```
Grup: deneme1213 (3 EOL)

Başlangıç:
- V710-FR-EOL: 0 / 120
- V710-LLS-EOL: 0 / 95  
- V710-MR-EOL: 0 / 150

1. V710-FR-EOL'de 15 dolly tara
   → Submit butonu aktif olur
   
2. V710-LLS-EOL'e geç, 8 dolly tara
   → Submit butonu hala aktif

3. Submit butonuna bas
   → Dialog gösterir:
     📍 V710-FR-EOL: 15 / 120
     📍 V710-LLS-EOL: 8 / 95
     Toplam: 23 / 215

4. Submit et
   → Başarılı mesajı
   → Grup listesine dön
```

#### Backend Field Uyumluluk Testi
```
Test 1: Tek EOL Endpoint (scanned field)
GET /api/manual-collection/groups/3/eols/11
Response: { "dollys": [{"scanned": true, ...}] }
✅ Dolly yeşil görünür

Test 2: Grup Endpoint (is_scanned field)
GET /api/manual-collection/groups/3
Response: { "eols": [{"dollys": [{"is_scanned": true, ...}]}] }
✅ Dolly yeşil görünür
```

### 📊 İstatistikler

- **Değişiklik:** 3 dosya
- **Güncellenen Dosyalar:** 
  - `GroupDetailActivity.java` (+80 satır)
  - `GroupDolly.java` (field annotation güncelleme)
  - `ManualSubmitRequest.java` (+15 satır)
  - `GroupDollysResponse.java` (nested structure)
- **Toplam Eklenen Satır:** ~95 satır
- **Silinen Satır:** ~5 satır

### 🚀 Deployment Notları

1. **Backend Gereksinimleri:**
   - `GET /api/manual-collection/groups/{groupId}` endpoint hazır olmalı
   - Response'da `is_scanned` field'ı doğru dönmeli (true/false)
   - `POST /api/manual-collection/mobile-submit` endpoint `group_name` field'ını kabul etmeli

2. **Mobil Uygulama:**
   - Eski tek-EOL submit ile uyumlu (backward compatible)
   - Grup endpoint kullanılamıyorsa graceful degradation
   - Debug logları production'da kapalı

3. **Test Checklist:**
   - [ ] Multi-EOL gruplarda submit testi
   - [ ] Tek EOL gruplarda submit testi
   - [ ] Backend field uyumluluk testi (`scanned` vs `is_scanned`)
   - [ ] Submit butonu aktif/pasif durumu testi
   - [ ] EOL'ler arası geçiş testi

### 📝 Bilinen Sorunlar

- Backend endpoint tutarsızlığı (bazı endpoint'ler `scanned`, bazıları `is_scanned` gönderiyor)
  - **Geçici Çözüm:** Mobil tarafta alternate field name desteği
  - **Kalıcı Çözüm:** Backend standardizasyonu (tüm endpoint'ler `is_scanned` kullanmalı)

### 🔜 Sonraki Adımlar

- [ ] Backend field standardizasyonu (`is_scanned` everywhere)
- [ ] Submit sonrası detaylı rapor ekranı
- [ ] Grup bazında progress tracking
- [ ] Submit history görüntüleme

---

## Version 1.2.0 - 9 Ocak 2026

### 🎯 Yeni Özellikler

#### 1. Toolbar ile Overflow Menü Sistemi
- ✅ **3 Nokta Menü** eklendi (modern Android UX)
- Alt kısımdaki butonlar menüye taşındı:
  - ✅ **Submit**: Dolly'leri gönder
  - 🔙 **Remove Last**: Son kaydı sil
  - 📦 **Manuel Dolly Ekle**: Sıradaki dolly'yi manuel ekle
- Ekran alanı optimize edildi (bottom bar kaldırıldı)

#### 2. Dolly Sıra Numarası Gösterimi
- ✅ **SEQ-001, SEQ-002** formatında sıra numarası gösterimi
- Ana başlık: Dolly sıra numarası (SEQ-001)
- Alt başlık: Dolly numarası (Dolly: 1062037)
- API'den `dolly_order_no` alanı eklendi
- Daha okunaklı ve anlaşılır dolly gösterimi

#### 3. Manuel Dolly Ekleme Validasyonu
- ✅ Sadece **sıradaki PENDING dolly** manuel eklenebilir
- Yanlış sırada ekleme denemesinde uyarı
- Dialog üzerinden doğrulama: Girilen numara ile sıradaki dolly eşleşmeli
- Hatalı girişte detaylı mesaj: "SEQ-003 (1062039) bekleniyor"

#### 4. Production Mode Aktivasyonu
- ✅ Test modu toast mesajları kaldırıldı
- API'den gelen gerçek hata mesajları gösteriliyor
- Sessiz başarılı okutma (sadece liste yenileniyor)
- Production'a hazır durum

### 🔧 İyileştirmeler

#### 1. VIN Sıralama Düzeltmesi
- ✅ VIN'ler **eklenme sırasına göre** gösteriliyor (alfabetik değil)
- API tarafında SQL sorgusu güncellendi
- Insertion order mantığı düzeltildi

#### 2. Gereksiz Validasyon Kontrolünün Kaldırılması
- ❌ `canScanDolly` client-side kontrolü kaldırıldı
- API kendi validasyonunu yapıyor
- Gereksiz bloklamalar ortadan kaldırıldı
- Kullanıcı deneyimi iyileştirildi

#### 3. UI/UX İyileştirmeleri
- Toolbar başlık: Grup adı gösteriliyor
- RecyclerView padding ayarlandı
- İki satırlı dolly gösterimi (sıra no + dolly no)
- Menü ikonları eklendi

### 📋 API Değişiklikleri

#### Güncellenen Model
```json
{
  "dolly_no": 1062037,
  "dolly_order_no": "SEQ-001",  // YENİ
  "first_vin": "ABC123",
  "last_vin": "XYZ789",
  "total_vins": 8,
  "status": "SCANNED"
}
```

### 🐛 Düzeltilen Hatalar
- ✅ VIN alfabetik sıralama hatası düzeltildi
- ✅ canScanDolly gereksiz bloklaması kaldırıldı
- ✅ Test modu toast'ları production'da görünmüyor
- ✅ Alt butonlar ekranı kapatmıyor

---

## Version 1.1.0 - 17 Aralık 2025

### 🎯 Yeni Özellikler

#### 1. Manuel Toplama Submit Sistemi
- ✅ **SUBMIT** butonu eklendi
- Operatör istediği yerde submit edebilir (tüm dolly'leri taramak zorunda değil)
- Submit öncesi onay dialogu: "Taranan dolly: X / Y"
- Başarılı submit sonrası detaylı bilgi gösterimi (Grup, Dolly Sayısı, Part Number)
- API Endpoint: `POST /api/manual-collection/submit`

#### 2. Sıralı Okutma Zorunluluğu
- ✅ Dolly'ler **üretim sırasına göre** taranmalı
- Backend'den gelen sıraya göre sadece ilk taranmamış dolly taranabilir
- Hatalı sırada tarama denemesinde uyarı: "⚠️ Lütfen sırayla tarayın! Önce '[dolly_no]' taranmalı"

#### 3. Dolly Duplikasyon Kontrolü
- ✅ Aynı dolly birden fazla kez taranamaz
- Zaten taranmış dolly için uyarı: "⚠ Bu kasa zaten tarandı: [dolly_no]"

#### 4. Gelişmiş Hata Yönetimi
- ✅ Backend hata mesajları JSON olarak parse ediliyor
- Kullanıcı dostu hata mesajları
- 401 (Unauthorized) durumunda otomatik login ekranına yönlendirme
- Detaylı hata dialogları (ağ hataları, backend hataları)

### 🔧 İyileştirmeler

#### 1. Auto-Refresh Sistemi
- Grup listesi her 1 saniyede otomatik yenileniyor
- Dolly listesi her 1 saniyede otomatik yenileniyor
- Activity pause olduğunda auto-refresh durur
- Activity resume olduğunda tekrar başlar

#### 2. API Yapılandırması
- Base URL güncellendi: `http://10.25.64.181:8181`
- Port: `8181`

#### 3. UI/UX İyileştirmeleri
- Submit butonu her zaman görünür ve aktif (en az 1 dolly tarandığında)
- Buton renkleri duruma göre değişiyor (yeşil = aktif)
- Loading göstergeleri tüm API çağrılarında
- Progress bar gösterimi

### 📋 API Değişiklikleri

#### Yeni Endpoint
```http
POST /api/manual-collection/submit
Authorization: Bearer <token>

Request:
{
  "group_name": "V710-MR-EOL"
}

Response:
{
  "success": true,
  "group_name": "V710-MR-EOL",
  "dolly_count": 8,
  "message": "Grup başarıyla tamamlandı",
  "part_number": "MANUEL-CUST123-V710MR-20251217-ABC"
}
```

#### Mevcut Endpoint'ler
- `GET /api/manual-collection/groups` - Grupları listele
- `GET /api/manual-collection/groups/{groupName}` - Grup dolly'lerini getir
- `POST /api/manual-collection/scan` - Dolly tara
- `POST /api/manual-collection/remove-last` - Son dolly'yi çıkar

### 🐛 Düzeltmeler

- ✅ Hata mesajlarının düzgün gösterilmemesi düzeltildi
- ✅ Auto-refresh sırasında memory leak'ler önlendi
- ✅ Session timeout kontrolü eklendi
- ✅ EditText focus sorunları çözüldü

### 📱 Yeni Model Sınıfları

```java
// API Models
- ManualSubmitRequest.java
- ManualSubmitResponse.java

// Adapter
- KasaAdapter.getData() metodu eklendi
```

### 🔍 Test Senaryoları

#### Sıralı Okutma Testi
```
Grup: V710-MR-EOL
Dollyler (Üretim sırası): [5170427, 5170428, 5170429]

✅ 5170427 tarar → Başarılı
❌ 5170429 tarar → "Önce 5170428 taranmalı"
✅ 5170428 tarar → Başarılı
✅ 5170429 tarar → Başarılı
```

#### Submit Testi
```
1. 3/8 dolly tarandı
2. SUBMIT butonuna bas
3. Dialog: "Taranan dolly: 3 / 8"
4. Submit'e bas
5. Success dialog göster
6. Grup listesine dön
```

#### Duplikasyon Testi
```
1. 5170427 tara → ✅ Başarılı
2. 5170427 tekrar tara → ❌ "Bu kasa zaten tarandı"
```

### 📊 İstatistikler

- **Toplam Değişiklik:** 6 dosya
- **Yeni Dosyalar:** 2 (ManualSubmitRequest, ManualSubmitResponse)
- **Güncellenen Dosyalar:** 4 (GroupDetailActivity, KasaAdapter, ForkliftApiService, activity_group_detail.xml)
- **Eklenen Satır:** ~250 satır
- **Silinen Satır:** ~50 satır

### 🚀 Deployment Notları

1. Backend API'nin hazır olduğundan emin olun:
   - `POST /api/manual-collection/submit` endpoint'i
   - Dolly'lerin üretim sırasına göre döndürüldüğü kontrol edilmeli

2. IP yapılandırması:
   - Base URL: `http://10.25.64.181:8181`
   - Prefs.java dosyasında default değer

3. Test öncesi kontroller:
   - Backend bağlantısı test edilmeli
   - Sample data ile sıralı okutma test edilmeli
   - Submit işlemi backend ile test edilmeli

### 📝 Bilinen Sorunlar

- Yok

### 🔜 Gelecek Sürüm Planları

- [ ] Offline mod desteği
- [ ] Toplu submit işlemi
- [ ] QR kod desteği
- [ ] Ses feedback
- [ ] Vibration feedback

---

**Geliştirici:** AI Assistant  
**Test:** Açık test - 18 Aralık 2025  
**Versiyon:** 1.1.0  
**Build:** Debug
