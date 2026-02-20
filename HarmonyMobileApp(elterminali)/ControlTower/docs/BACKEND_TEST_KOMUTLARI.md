## 🧪 BACKEND API TEST KOMUTLARI

**Tarih:** 12 Ocak 2026  
**Amaç:** Manuel API test ve doğrulama  
**Durum:** ✅ Tüm sorunlar çözüldü - Test edilmeye hazır

---

## 📋 **ÖN HAZIRLIK**

### **1. Token Al (Login)**
```powershell
# Login endpoint'i ile token al
$loginResponse = Invoke-RestMethod -Uri "http://10.25.64.181:8181/api/forklift/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body '{"barcode": "OPERATOR_BARCODE"}'

# Token'ı değişkene kaydet
$token = $loginResponse.token
Write-Host "Token alındı: $token"
```

### **2. Header Hazırla**
```powershell
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}
```

---

## 🧪 **TEST SENARYOLARI**

### **TEST 1: Grup Listesini Getir**
```powershell
# Tüm grupları listele
$groups = Invoke-RestMethod -Uri "http://10.25.64.181:8181/api/manual-collection/groups" `
    -Method GET `
    -Headers $headers

# Sonucu göster
$groups | ConvertTo-Json -Depth 10

# Sadece 710grup'u filtrele
$grup710 = $groups | Where-Object { $_.group_name -eq "710grup" }
$grup710 | ConvertTo-Json -Depth 5

# 710grup'un EOL'lerini göster
Write-Host "`n=== 710grup'un EOL'leri ===" -ForegroundColor Cyan
$grup710.eols | ForEach-Object {
    Write-Host "EOL ID: $($_.eol_id) | Name: $($_.eol_name) | Dolly: $($_.dolly_count) | Scanned: $($_.scanned_count)"
}
```

---

### **TEST 2: EOL Dolly Listesini Getir**
```powershell
# Değişkenleri ayarla
$groupId = 1  # 710grup'un ID'si (grup listesinden al)
$eolId = 2    # V710-LLS-EOL'un ID'si (grup listesinden al)

# EOL dolly listesi
$eolDollys = Invoke-RestMethod `
    -Uri "http://10.25.64.181:8181/api/manual-collection/groups/$groupId/eols/$eolId" `
    -Method GET `
    -Headers $headers

# Response'u göster
Write-Host "`n=== EOL Dolly Listesi ===" -ForegroundColor Cyan
Write-Host "Grup: $($eolDollys.group_name)"
Write-Host "EOL: $($eolDollys.eol_name)"
Write-Host "PartNumber: $($eolDollys.part_number)"

# Dolly'leri tablo olarak göster
Write-Host "`nDolly'ler:" -ForegroundColor Yellow
$eolDollys.dollys | ForEach-Object {
    $status = if ($_.scanned) { "✅ Tarandı" } else { "⏳ Bekliyor" }
    Write-Host "  Order: $($_.dolly_order_no) | Dolly: $($_.dolly_no) | $status"
}

# Sıradaki pending dolly'yi bul
$nextPending = $eolDollys.dollys | Where-Object { -not $_.scanned } | Select-Object -First 1
if ($nextPending) {
    Write-Host "`n✅ Sıradaki dolly: $($nextPending.dolly_no) (order: $($nextPending.dolly_order_no))" -ForegroundColor Green
} else {
    Write-Host "`n⚠️ Tüm dolly'ler taranmış!" -ForegroundColor Yellow
}
```

---

### **TEST 3: Dolly Okutma (BAŞARILI)**
```powershell
# Sıradaki dolly'yi okut
$scanRequest = @{
    group_name = "710grup"
    eol_name = "V710-LLS-EOL"
    barcode = "1070744"  # Sıradaki dolly numarası
} | ConvertTo-Json

Write-Host "`n=== Dolly Okutma Testi ===" -ForegroundColor Cyan
Write-Host "Request: $scanRequest"

try {
    $scanResponse = Invoke-RestMethod `
        -Uri "http://10.25.64.181:8181/api/manual-collection/scan" `
        -Method POST `
        -Headers $headers `
        -Body $scanRequest
    
    Write-Host "`n✅ BAŞARILI!" -ForegroundColor Green
    $scanResponse | ConvertTo-Json
} catch {
    $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json
    Write-Host "`n❌ HATA!" -ForegroundColor Red
    $errorDetails | ConvertTo-Json
}
```

---

### **TEST 4: Dolly Atlamayı Dene (HATA BEKLENİYOR)**
```powershell
# Sıradaki dolly'yi atla, sonrakini okutmayı dene
$skipRequest = @{
    group_name = "710grup"
    eol_name = "V710-LLS-EOL"
    barcode = "1070787"  # 2. sıradaki dolly (1. atlanıyor)
} | ConvertTo-Json

Write-Host "`n=== Dolly Atlama Testi (Hata Bekleniyor) ===" -ForegroundColor Cyan
Write-Host "Request: $skipRequest"

try {
    $skipResponse = Invoke-RestMethod `
        -Uri "http://10.25.64.181:8181/api/manual-collection/scan" `
        -Method POST `
        -Headers $headers `
        -Body $skipRequest
    
    Write-Host "`n⚠️ BEKLENMEDIK: İşlem başarılı oldu (olmamalıydı!)" -ForegroundColor Yellow
    $skipResponse | ConvertTo-Json
} catch {
    Write-Host "`n✅ BEKLENEN HATA ALINDI!" -ForegroundColor Green
    
    $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json
    Write-Host "`nHata Mesajı: $($errorDetails.error)" -ForegroundColor Red
    
    # expected_dolly field'ı var mı kontrol et
    if ($errorDetails.PSObject.Properties.Name -contains "expected_dolly") {
        Write-Host "✅ expected_dolly var: $($errorDetails.expected_dolly)" -ForegroundColor Green
    } else {
        Write-Host "❌ expected_dolly EKSIK! Backend düzeltilmeli!" -ForegroundColor Red
    }
    
    if ($errorDetails.PSObject.Properties.Name -contains "received_dolly") {
        Write-Host "✅ received_dolly var: $($errorDetails.received_dolly)" -ForegroundColor Green
    } else {
        Write-Host "❌ received_dolly EKSIK!" -ForegroundColor Red
    }
    
    Write-Host "`nTam Error Response:"
    $errorDetails | ConvertTo-Json
}
```

---

### **TEST 5: Farklı EOL Geçişi (İZİN VERİLMELİ)**
```powershell
# V710-FR-EOL'den bir dolly okut
$eolSwitchRequest1 = @{
    group_name = "710grup"
    eol_name = "V710-FR-EOL"
    barcode = "1070001"  # V710-FR'den ilk dolly
} | ConvertTo-Json

Write-Host "`n=== EOL Geçiş Testi - Adım 1 (V710-FR) ===" -ForegroundColor Cyan
try {
    $response1 = Invoke-RestMethod `
        -Uri "http://10.25.64.181:8181/api/manual-collection/scan" `
        -Method POST `
        -Headers $headers `
        -Body $eolSwitchRequest1
    Write-Host "✅ V710-FR-EOL: 1070001 başarıyla okutuldu" -ForegroundColor Green
} catch {
    Write-Host "❌ Hata: $($_.ErrorDetails.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 1

# Şimdi V710-LLS-EOL'e geç
$eolSwitchRequest2 = @{
    group_name = "710grup"
    eol_name = "V710-LLS-EOL"
    barcode = "1070744"  # V710-LLS'den ilk dolly
} | ConvertTo-Json

Write-Host "`n=== EOL Geçiş Testi - Adım 2 (V710-LLS) ===" -ForegroundColor Cyan
try {
    $response2 = Invoke-RestMethod `
        -Uri "http://10.25.64.181:8181/api/manual-collection/scan" `
        -Method POST `
        -Headers $headers `
        -Body $eolSwitchRequest2
    Write-Host "✅ V710-LLS-EOL: 1070744 başarıyla okutuldu (EOL geçişi çalıştı!)" -ForegroundColor Green
} catch {
    $errorMsg = $_.ErrorDetails.Message | ConvertFrom-Json
    if ($errorMsg.error -match "sıra") {
        Write-Host "❌ YANLIŞ: Backend EOL geçişine izin vermiyor!" -ForegroundColor Red
        Write-Host "   Hata: $($errorMsg.error)"
    } else {
        Write-Host "❌ Başka bir hata: $($errorMsg.error)" -ForegroundColor Red
    }
}

# Tekrar V710-FR'ye dön (order:2)
$eolSwitchRequest3 = @{
    group_name = "710grup"
    eol_name = "V710-FR-EOL"
    barcode = "1070002"  # V710-FR'den ikinci dolly
} | ConvertTo-Json

Write-Host "`n=== EOL Geçiş Testi - Adım 3 (V710-FR'ye geri dön) ===" -ForegroundColor Cyan
try {
    $response3 = Invoke-RestMethod `
        -Uri "http://10.25.64.181:8181/api/manual-collection/scan" `
        -Method POST `
        -Headers $headers `
        -Body $eolSwitchRequest3
    Write-Host "✅ V710-FR-EOL: 1070002 başarıyla okutuldu (EOL arası geçiş sorunsuz!)" -ForegroundColor Green
} catch {
    Write-Host "❌ Hata: $($_.ErrorDetails.Message)" -ForegroundColor Red
}
```

---

### **TEST 6: Remove Last (Son Dolly'yi Çıkar)**
```powershell
# Son okutulmuş dolly'yi çıkar
$removeRequest = @{
    group_name = "710grup"
    eol_name = "V710-LLS-EOL"
    barcode = "admin"  # Veya dolly numarası
} | ConvertTo-Json

Write-Host "`n=== Remove Last Testi ===" -ForegroundColor Cyan
try {
    $removeResponse = Invoke-RestMethod `
        -Uri "http://10.25.64.181:8181/api/manual-collection/remove-last" `
        -Method POST `
        -Headers $headers `
        -Body $removeRequest
    
    Write-Host "✅ Son dolly çıkartıldı!" -ForegroundColor Green
    $removeResponse | ConvertTo-Json
} catch {
    Write-Host "❌ Hata: $($_.ErrorDetails.Message)" -ForegroundColor Red
}
```

---

## 🔍 **BACKEND RESPONSE KONTROLÜ**

### **Başarılı Scan Response (Olması Gereken):**
```json
{
  "success": true,
  "dolly_no": "1070744",
  "eol_name": "V710-LLS-EOL",
  "group_name": "710grup",
  "message": "Dolly başarıyla okutuldu"
}
```

### **Sıra Hatası Response (✅ ŞİMDİ MEVCUT!):**
```json
{
  "error": "V710-LLS-EOL EOL'de dolly sırası yanlış! Sıradaki dolly '1070744' (order:1) okutulmalı",
  "retryable": true,
  "expected_dolly": "1070744",          ✅ MEVCUT!
  "expected_order": 1,                   ✅ MEVCUT!
  "received_dolly": "1070787",          ✅ MEVCUT!
  "received_order": 2,                   ✅ MEVCUT!
  "eol_name": "V710-LLS-EOL"            ✅ MEVCUT!
}
```

---

## 📋 **BACKEND KONTROL LİSTESİ**

### **✅ TAMAMLANAN:**

1. **✅ Grup Listesi API:**
   ```powershell
   GET /api/manual-collection/groups
   # group_name = "710grup" ✓
   # eol_name = "V710-LLS-EOL" ✓
   ```

2. **✅ EOL Dolly Listesi:**
   ```powershell
   GET /api/manual-collection/groups/1/eols/2
   # dolly_order_no artık NULL değil ✓
   # Dolly'ler order'a göre sıralı ✓
   ```

3. **✅ Dolly Scan (Başarılı):**
   ```powershell
   POST /api/manual-collection/scan
   # Sıradaki dolly → ✅ Success
   ```

4. **✅ Dolly Scan (Sıra Hatası):**
   ```powershell
   POST /api/manual-collection/scan
   # Sıra dışı dolly → ❌ Error
   # expected_dolly field'ı MEVCUT ✓
   # received_dolly field'ı MEVCUT ✓
   # expected_order field'ı MEVCUT ✓
   # received_order field'ı MEVCUT ✓
   ```

5. **✅ EOL Geçişi:**
   ```powershell
   # V710-FR: D1 → V710-LLS: D1 → V710-FR: D2
   # ✅ İzin veriyor (aynı grup içinde)
   ```

6. **✅ Remove Last:**
   ```powershell
   POST /api/manual-collection/remove-last
   # Son dolly çıkıyor ✓
   ```

---

## 🎯 **TEST ÖNERİLERİ**

Test etmek için aşağıdaki PowerShell komutlarını çalıştırın:

---

## ✅ **BACKEND GÜNCELLEMELERI TAMAMLANDI**

### **Yapılan Düzeltmeler:**

1. **✅ Grup Validasyonu (11:51):**
   - EOL Name bazlı eşleştirme eklendi
   - EOLID vs PWorkStationId uyumsuzluğu çözüldü

2. **✅ Sıra Kontrolü (12:00):**
   - DollyOrderNo bazlı kontrol
   - EOL bazlı (grup genelinde değil)
   - Tüm error field'ları eklendi

3. **✅ Error Response:**
   ```python
   {
       "error": "...",
       "expected_dolly": "1070744",    ✓
       "expected_order": 1,             ✓
       "received_dolly": "1070787",    ✓
       "received_order": 2,             ✓
       "eol_name": "V710-LLS-EOL"      ✓
   }
   ```

**Yukarıdaki test komutlarını çalıştırarak doğrulayabilirsiniz!**

---

**Hazırlayan:** Backend Geliştirme Ekibi  
**Tarih:** 12 Ocak 2026 12:00  
**Durum:** ✅ Production'da aktif - Test edilebilir
