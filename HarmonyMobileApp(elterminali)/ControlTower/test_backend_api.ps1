# Backend API Sequence Error Test
# Bu script backend'in expected_dolly, received_dolly vb. alanları gönderip göndermediğini test eder

Write-Host "Backend API Test Başlıyor..." -ForegroundColor Green
Write-Host "====================================`n"

# 1. LOGIN
Write-Host "[1/4] Login..." -ForegroundColor Cyan
$loginBody = '{"operatorBarcode":"JkE4Ttgog6R3vpir","deviceId":"PowerShellTest"}'
try {
    $login = Invoke-RestMethod -Uri "http://10.25.64.181:8181/api/forklift/login" -Method POST -ContentType "application/json" -Body $loginBody
    $token = $login.sessionToken
    Write-Host "      ✓ Token alındı" -ForegroundColor Green
    Write-Host "      Operator: $($login.operatorName)" -ForegroundColor Gray
} catch {
    Write-Host "      ✗ Login başarısız: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. GET GROUPS
Write-Host "`n[2/4] Gruplar alınıyor..." -ForegroundColor Cyan
$headers = @{"Authorization"="Bearer $token"}
try {
    $groups = Invoke-RestMethod -Uri "http://10.25.64.181:8181/api/manual-collection/groups" -Headers $headers
    $group = $groups[0]
    $eol = $group.eols[0]
    Write-Host "      ✓ Grup: $($group.group_name)" -ForegroundColor Green
    Write-Host "      ✓ EOL: $($eol.eol_name) (ID: $($eol.eol_id))" -ForegroundColor Green
} catch {
    Write-Host "      ✗ Grup listesi alınamadı: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 3. GET DOLLYS
Write-Host "`n[3/4] Dolly listesi alınıyor..." -ForegroundColor Cyan
try {
    $dollysResp = Invoke-RestMethod -Uri "http://10.25.64.181:8181/api/manual-collection/groups/$($group.group_id)/eols/$($eol.eol_id)" -Headers $headers
    $dolly1 = $dollysResp.dollys[0]
    $dolly3 = $dollysResp.dollys[2]
    Write-Host "      ✓ Toplam dolly: $($dollysResp.dollys.Count)" -ForegroundColor Green
    Write-Host "      ✓ 1. sıra: $($dolly1.dolly_no) (order: $($dolly1.dolly_order))" -ForegroundColor Green
    Write-Host "      ✓ 3. sıra: $($dolly3.dolly_no) (order: $($dolly3.dolly_order))" -ForegroundColor Green
} catch {
    Write-Host "      ✗ Dolly listesi alınamadı: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 4. TEST SEQUENCE ERROR
Write-Host "`n[4/4] SIRA HATASI TESTİ..." -ForegroundColor Magenta
Write-Host "      1. sıradaki bekleniyor: $($dolly1.dolly_no)" -ForegroundColor Gray
Write-Host "      Ama 3. sıradakini okutuyorum: $($dolly3.dolly_no)" -ForegroundColor Gray

$scanBody = @{
    group_name = $group.group_name
    eol_name = $eol.eol_name
    barcode = $dolly3.dolly_no
} | ConvertTo-Json

try {
    $scanResp = Invoke-RestMethod -Uri "http://10.25.64.181:8181/api/manual-collection/scan" -Method POST -Headers $headers -ContentType "application/json" -Body $scanBody
    Write-Host "`n      ⚠ UYARI: Backend hata vermedi (vermesi gerekiyordu)!" -ForegroundColor Red
    Write-Host "      Response: $($scanResp | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    $errorResp = $_.ErrorDetails.Message | ConvertFrom-Json
    
    Write-Host "`n      ✓ Hata alındı (beklenen durum)" -ForegroundColor Green
    Write-Host "      Hata mesajı: $($errorResp.error)" -ForegroundColor Gray
    
    Write-Host "`n====================================`n"
    Write-Host "BACKEND RESPONSE ALANLARI:" -ForegroundColor Cyan
    Write-Host "====================================`n"
    
    $allFieldsPresent = $true
    
    # expected_dolly
    if ($errorResp.PSObject.Properties.Name -contains "expected_dolly") {
        Write-Host "✅ expected_dolly: '$($errorResp.expected_dolly)'" -ForegroundColor Green
    } else {
        Write-Host "❌ expected_dolly: EKSIK!" -ForegroundColor Red
        $allFieldsPresent = $false
    }
    
    # received_dolly
    if ($errorResp.PSObject.Properties.Name -contains "received_dolly") {
        Write-Host "✅ received_dolly: '$($errorResp.received_dolly)'" -ForegroundColor Green
    } else {
        Write-Host "❌ received_dolly: EKSIK!" -ForegroundColor Red
        $allFieldsPresent = $false
    }
    
    # expected_order
    if ($errorResp.PSObject.Properties.Name -contains "expected_order") {
        Write-Host "✅ expected_order: $($errorResp.expected_order)" -ForegroundColor Green
    } else {
        Write-Host "❌ expected_order: EKSIK!" -ForegroundColor Red
        $allFieldsPresent = $false
    }
    
    # received_order
    if ($errorResp.PSObject.Properties.Name -contains "received_order") {
        Write-Host "✅ received_order: $($errorResp.received_order)" -ForegroundColor Green
    } else {
        Write-Host "❌ received_order: EKSIK!" -ForegroundColor Red
        $allFieldsPresent = $false
    }
    
    # eol_name
    if ($errorResp.PSObject.Properties.Name -contains "eol_name") {
        Write-Host "✅ eol_name: '$($errorResp.eol_name)'" -ForegroundColor Green
    } else {
        Write-Host "❌ eol_name: EKSIK!" -ForegroundColor Red
        $allFieldsPresent = $false
    }
    
    Write-Host "`n====================================`n"
    
    # Final sonuç
    if ($allFieldsPresent) {
        Write-Host "🎉 TEST BAŞARILI!" -ForegroundColor Green
        Write-Host "Backend tüm gerekli alanları gönderiyor." -ForegroundColor Green
        Write-Host "Mobil app backend verilerini doğrudan kullanabilir." -ForegroundColor Yellow
    } else {
        Write-Host "⚠ TEST BAŞARISIZ!" -ForegroundColor Red
        Write-Host "Backend bazı alanları göndermiyor." -ForegroundColor Red
        Write-Host "Mobil app fallback mekanizmasını kullanacak (getNextPendingDolly)." -ForegroundColor Yellow
    }
    
    Write-Host "`n====================================`n"
    Write-Host "TÜM RESPONSE ALANLARI:" -ForegroundColor Cyan
    $errorResp.PSObject.Properties | ForEach-Object {
        Write-Host "  - $($_.Name): $($_.Value)" -ForegroundColor Gray
    }
}
