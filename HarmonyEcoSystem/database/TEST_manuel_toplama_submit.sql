-- ============================================
-- TEST SCRIPT: Manuel Toplama Submit İşlemi
-- ============================================
-- Bu script manuel toplama submit işlemini test eder
-- KULLANIM: JIS üretimde kullanılacak, hata yapamayız!

-- =====================
-- 1. TEST VERISI HAZIRLA
-- =====================

-- Önce test dolly'lerini ekle (eğer yoksa)
IF NOT EXISTS (SELECT 1 FROM DollyEOLInfo WHERE DollyNo = 'TEST-DOLLY-001')
BEGIN
    INSERT INTO DollyEOLInfo (DollyNo, VinNo, DollyOrderNo, CustomerReferans, Adet, EOLName, EOLID, EOLDATE, InsertedAt)
    VALUES 
        ('TEST-DOLLY-001', 'TEST-VIN-001', 'DO-001', 'CUST-001', 1, 'TEST-EOL-A', 'EOL-001', GETDATE(), GETDATE()),
        ('TEST-DOLLY-001', 'TEST-VIN-002', 'DO-001', 'CUST-001', 1, 'TEST-EOL-A', 'EOL-001', GETDATE(), GETDATE()),
        ('TEST-DOLLY-001', 'TEST-VIN-003', 'DO-001', 'CUST-001', 1, 'TEST-EOL-A', 'EOL-001', GETDATE(), GETDATE());
    
    PRINT '✅ Test dolly verisi eklendi: TEST-DOLLY-001 (3 VIN)';
END
ELSE
BEGIN
    PRINT 'ℹ️ Test dolly zaten mevcut';
END;
GO

-- =====================
-- 2. SUBMIT ÖNCESİ DURUM
-- =====================

PRINT '📊 SUBMIT ÖNCESİ DURUM:';
PRINT '========================';

SELECT COUNT(*) AS 'DollyEOLInfo - Toplam VIN'
FROM DollyEOLInfo
WHERE DollyNo = 'TEST-DOLLY-001';

SELECT COUNT(*) AS 'DollySubmissionHold - Toplam VIN'
FROM DollySubmissionHold
WHERE DollyNo = 'TEST-DOLLY-001';

GO

-- =====================
-- 3. SUBMIT İŞLEMİ (Manuel)
-- =====================

-- MANUEL SUBMIT SİMÜLASYONU
-- Python API'sinin yaptığı işlemleri simüle ediyoruz

BEGIN TRANSACTION;

DECLARE @DollyNo NVARCHAR(20) = 'TEST-DOLLY-001';
DECLARE @TerminalUser NVARCHAR(100) = 'TEST-USER';
DECLARE @ScanOrder INT = 1;
DECLARE @Errors INT = 0;

-- Her VIN için işlem yap
DECLARE @VinNo NVARCHAR(50);
DECLARE vin_cursor CURSOR FOR
    SELECT VinNo FROM DollyEOLInfo WHERE DollyNo = @DollyNo;

OPEN vin_cursor;
FETCH NEXT FROM vin_cursor INTO @VinNo;

WHILE @@FETCH_STATUS = 0
BEGIN
    -- 1. Check if VIN exists in DollyEOLInfo
    IF NOT EXISTS (SELECT 1 FROM DollyEOLInfo WHERE DollyNo = @DollyNo AND VinNo = @VinNo)
    BEGIN
        PRINT '❌ HATA: VIN bulunamadı: ' + @VinNo;
        SET @Errors = @Errors + 1;
        BREAK;
    END

    -- 2. Check if already in DollySubmissionHold
    IF EXISTS (SELECT 1 FROM DollySubmissionHold WHERE DollyNo = @DollyNo AND VinNo = @VinNo)
    BEGIN
        PRINT '❌ HATA: VIN zaten submit edilmiş: ' + @VinNo;
        SET @Errors = @Errors + 1;
        BREAK;
    END

    -- 3. INSERT into DollySubmissionHold
    INSERT INTO DollySubmissionHold (
        DollyNo, VinNo, Status, DollyOrderNo, CustomerReferans, 
        EOLName, EOLID, Adet, ScanOrder, TerminalUser, CreatedAt, UpdatedAt
    )
    SELECT 
        DollyNo, VinNo, 'pending', DollyOrderNo, CustomerReferans,
        EOLName, EOLID, Adet, @ScanOrder, @TerminalUser, GETDATE(), GETDATE()
    FROM DollyEOLInfo
    WHERE DollyNo = @DollyNo AND VinNo = @VinNo;

    -- 4. DELETE from DollyEOLInfo
    DELETE FROM DollyEOLInfo
    WHERE DollyNo = @DollyNo AND VinNo = @VinNo;

    PRINT '✅ VIN işlendi: ' + @VinNo;

    FETCH NEXT FROM vin_cursor INTO @VinNo;
END;

CLOSE vin_cursor;
DEALLOCATE vin_cursor;

-- Hata varsa rollback
IF @Errors > 0
BEGIN
    ROLLBACK TRANSACTION;
    PRINT '❌ TRANSACTION ROLLBACK: Hatalar bulundu!';
END
ELSE
BEGIN
    COMMIT TRANSACTION;
    PRINT '✅ TRANSACTION COMMIT: Tüm VIN''ler başarıyla submit edildi!';
END;

GO

-- =====================
-- 4. SUBMIT SONRASI DURUM
-- =====================

PRINT '';
PRINT '📊 SUBMIT SONRASI DURUM:';
PRINT '========================';

SELECT COUNT(*) AS 'DollyEOLInfo - Toplam VIN (0 olmalı)'
FROM DollyEOLInfo
WHERE DollyNo = 'TEST-DOLLY-001';

SELECT COUNT(*) AS 'DollySubmissionHold - Toplam VIN (3 olmalı)'
FROM DollySubmissionHold
WHERE DollyNo = 'TEST-DOLLY-001';

-- Detaylı kontrol
SELECT 
    DollyNo, VinNo, Status, ScanOrder, TerminalUser, CreatedAt
FROM DollySubmissionHold
WHERE DollyNo = 'TEST-DOLLY-001'
ORDER BY VinNo;

GO

-- =====================
-- 5. TEMİZLİK (TEST SONRASI)
-- =====================

PRINT '';
PRINT '🧹 Test verilerini temizle (opsiyonel):';
PRINT '-- DELETE FROM DollySubmissionHold WHERE DollyNo = ''TEST-DOLLY-001'';';
PRINT '-- Test tamamlandıktan sonra yukarıdaki komutu çalıştırabilirsiniz.';

GO
