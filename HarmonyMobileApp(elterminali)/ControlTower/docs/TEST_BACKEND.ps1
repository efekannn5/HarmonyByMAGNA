# 🧪 BACKEND API TEST SCRIPT
# Tarih: 12 Ocak 2026
# Amaç: Manuel Collection API test

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  BACKEND API TEST - Manuel Collection" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. LOGIN (Operatör barkodunu gir)
Write-Host "1️⃣  LOGIN İŞLEMİ" -ForegroundColor Yellow
$operatorBarcode = Read-Host "Operatör barkodunu girin"

try {
    $loginResponse = Invoke-RestMethod `
        -Uri "http://10.25.64.181:8181/api/forklift/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body "{`"barcode`": `"$operatorBarcode`"}"
    
    $token = $loginResponse.token
    Write-Host "✅ Login başarılı! Token alındı.`n" -ForegroundColor Green
} catch {
    Write-Host "❌ Login başarısız!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit
}

# Header hazırla
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# 2. GRUP LİSTESİ
Write-Host "2️⃣  GRUP LİSTESİNİ GETİR" -ForegroundColor Yellow
try {
    $groups = Invoke-RestMethod `
        -Uri "http://10.25.64.181:8181/api/manual-collection/groups" `
        -Method GET `
        -Headers $headers
    
    Write-Host "✅ Grup listesi alındı!`n" -ForegroundColor Green
    
    # 710grup'u bul
    $grup710 = $groups | Where-Object { $_.group_name -eq "710grup" }
    if ($grup710) {
        Write-Host "=== 710grup Detayları ===" -ForegroundColor Cyan
        Write-Host "  Grup ID: $($grup710.group_id)"
        Write-Host "  Grup Adı: $($grup710.group_name)"
        Write-Host "  PartNumber: $($grup710.part_number)"
        Write-Host "  Toplam Dolly: $($grup710.total_dolly_count)"
        Write-Host "  Taranan: $($grup710.total_scanned_count)`n"
        
        Write-Host "  EOL'ler:" -ForegroundColor Yellow
        $grup710.eols | ForEach-Object {
            Write-Host "    - ID: $($_.eol_id) | $($_.eol_name) | Dolly: $($_.dolly_count) | Taranan: $($_.scanned_count)"
        }
        Write-Host ""
    } else {
        Write-Host "⚠️  710grup bulunamadı!`n" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Grup listesi alınamadı!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

# 3. EOL DOLLY LİSTESİ
Write-Host "`n3️⃣  EOL DOLLY LİSTESİNİ GETİR" -ForegroundColor Yellow
$groupId = Read-Host "Grup ID girin (örn: $($grup710.group_id))"
$eolId = Read-Host "EOL ID girin (örn: 2 - V710-LLS-EOL)"

try {
    $eolDollys = Invoke-RestMethod `
        -Uri "http://10.25.64.181:8181/api/manual-collection/groups/$groupId/eols/$eolId" `
        -Method GET `
        -Headers $headers
    
    Write-Host "✅ EOL dolly listesi alındı!`n" -ForegroundColor Green
    Write-Host "=== $($eolDollys.eol_name) Dolly Listesi ===" -ForegroundColor Cyan
    Write-Host "  Grup: $($eolDollys.group_name)"
    Write-Host "  EOL: $($eolDollys.eol_name)"
    Write-Host "  PartNumber: $($eolDollys.part_number)`n"
    
    Write-Host "  Dolly'ler:" -ForegroundColor Yellow
    $eolDollys.dollys | ForEach-Object {
        $status = if ($_.scanned) { "✅ Tarandı" } else { "⏳ Bekliyor" }
        Write-Host "    Order: $($_.dolly_order_no) | Dolly: $($_.dolly_no) | $status"
    }
    
    # Sıradaki pending dolly
    $nextPending = $eolDollys.dollys | Where-Object { -not $_.scanned } | Select-Object -First 1
    if ($nextPending) {
        Write-Host "`n  ✅ Sıradaki dolly: $($nextPending.dolly_no) (order: $($nextPending.dolly_order_no))" -ForegroundColor Green
    } else {
        Write-Host "`n  ⚠️  Tüm dolly'ler taranmış!" -ForegroundColor Yellow
    }
    Write-Host ""
} catch {
    Write-Host "❌ EOL dolly listesi alınamadı!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

# 4. TEST SEÇİMİ
Write-Host "`n4️⃣  TEST SEÇİMİ" -ForegroundColor Yellow
Write-Host "1) Başarılı scan (sıradaki dolly)"
Write-Host "2) Başarısız scan (dolly atlamak - hata bekleniyor)"
Write-Host "3) EOL geçişi (farklı EOL'den dolly)"
$testChoice = Read-Host "Test seçin (1/2/3)"

$groupName = $eolDollys.group_name
$eolName = $eolDollys.eol_name

switch ($testChoice) {
    "1" {
        # Başarılı scan
        Write-Host "`n=== TEST: Başarılı Scan ===" -ForegroundColor Cyan
        $barcode = Read-Host "Sıradaki dolly barkodu girin (örn: $($nextPending.dolly_no))"
        
        $scanBody = @{
            group_name = $groupName
            eol_name = $eolName
            barcode = $barcode
        } | ConvertTo-Json
        
        try {
            $scanResponse = Invoke-RestMethod `
                -Uri "http://10.25.64.181:8181/api/manual-collection/scan" `
                -Method POST `
                -Headers $headers `
                -Body $scanBody
            
            Write-Host "`n✅ BAŞARILI!" -ForegroundColor Green
            Write-Host "  Dolly: $($scanResponse.dolly_no)"
            Write-Host "  EOL: $($scanResponse.eol_name)"
            Write-Host "  Grup: $($scanResponse.group_name)"
            Write-Host "  Mesaj: $($scanResponse.message)`n"
        } catch {
            $errorResponse = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "`n❌ HATA!" -ForegroundColor Red
            Write-Host "  Mesaj: $($errorResponse.error)`n" -ForegroundColor Red
        }
    }
    
    "2" {
        # Başarısız scan (dolly atlamak)
        Write-Host "`n=== TEST: Dolly Atlama (Hata Bekleniyor) ===" -ForegroundColor Cyan
        $skipBarcode = Read-Host "2. veya 3. sıradaki dolly barkodu girin"
        
        $skipBody = @{
            group_name = $groupName
            eol_name = $eolName
            barcode = $skipBarcode
        } | ConvertTo-Json
        
        try {
            $skipResponse = Invoke-RestMethod `
                -Uri "http://10.25.64.181:8181/api/manual-collection/scan" `
                -Method POST `
                -Headers $headers `
                -Body $skipBody
            
            Write-Host "`n⚠️  BEKLENMEDIK: İşlem başarılı oldu (olmamalıydı!)" -ForegroundColor Yellow
            $skipResponse | ConvertTo-Json
        } catch {
            Write-Host "`n✅ BEKLENEN HATA ALINDI!" -ForegroundColor Green
            $errorResponse = $_.ErrorDetails.Message | ConvertFrom-Json
            
            Write-Host "`n  Hata Mesajı:" -ForegroundColor Yellow
            Write-Host "    $($errorResponse.error)`n" -ForegroundColor Red
            
            # Field kontrolü
            Write-Host "  Backend Response Kontrolü:" -ForegroundColor Yellow
            
            if ($errorResponse.PSObject.Properties.Name -contains "expected_dolly" -and $errorResponse.expected_dolly) {
                Write-Host "    ✅ expected_dolly: $($errorResponse.expected_dolly)" -ForegroundColor Green
            } else {
                Write-Host "    ❌ expected_dolly EKSIK veya NULL!" -ForegroundColor Red
            }
            
            if ($errorResponse.PSObject.Properties.Name -contains "expected_order" -and $errorResponse.expected_order) {
                Write-Host "    ✅ expected_order: $($errorResponse.expected_order)" -ForegroundColor Green
            } else {
                Write-Host "    ❌ expected_order EKSIK veya NULL!" -ForegroundColor Red
            }
            
            if ($errorResponse.PSObject.Properties.Name -contains "received_dolly" -and $errorResponse.received_dolly) {
                Write-Host "    ✅ received_dolly: $($errorResponse.received_dolly)" -ForegroundColor Green
            } else {
                Write-Host "    ❌ received_dolly EKSIK veya NULL!" -ForegroundColor Red
            }
            
            if ($errorResponse.PSObject.Properties.Name -contains "received_order" -and $errorResponse.received_order) {
                Write-Host "    ✅ received_order: $($errorResponse.received_order)" -ForegroundColor Green
            } else {
                Write-Host "    ❌ received_order EKSIK veya NULL!" -ForegroundColor Red
            }
            
            if ($errorResponse.PSObject.Properties.Name -contains "eol_name" -and $errorResponse.eol_name) {
                Write-Host "    ✅ eol_name: $($errorResponse.eol_name)" -ForegroundColor Green
            } else {
                Write-Host "    ❌ eol_name EKSIK veya NULL!" -ForegroundColor Red
            }
            
            Write-Host "`n  Tam Error Response:" -ForegroundColor Yellow
            $errorResponse | ConvertTo-Json | Write-Host
        }
    }
    
    "3" {
        # EOL geçişi
        Write-Host "`n=== TEST: EOL Geçişi ===" -ForegroundColor Cyan
        $otherEol = Read-Host "Farklı EOL adı girin (örn: V710-FR-EOL)"
        $otherBarcode = Read-Host "O EOL'den 1. sıradaki dolly barkodu girin"
        
        $eolSwitchBody = @{
            group_name = $groupName
            eol_name = $otherEol
            barcode = $otherBarcode
        } | ConvertTo-Json
        
        try {
            $switchResponse = Invoke-RestMethod `
                -Uri "http://10.25.64.181:8181/api/manual-collection/scan" `
                -Method POST `
                -Headers $headers `
                -Body $eolSwitchBody
            
            Write-Host "`n✅ BAŞARILI! EOL geçişi izin verildi!" -ForegroundColor Green
            Write-Host "  Dolly: $($switchResponse.dolly_no)"
            Write-Host "  EOL: $($switchResponse.eol_name)"
            Write-Host "  Grup: $($switchResponse.group_name)`n"
        } catch {
            $errorResponse = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "`n❌ HATA! EOL geçişine izin verilmedi!" -ForegroundColor Red
            Write-Host "  Mesaj: $($errorResponse.error)`n" -ForegroundColor Red
        }
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  TEST TAMAMLANDI" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
