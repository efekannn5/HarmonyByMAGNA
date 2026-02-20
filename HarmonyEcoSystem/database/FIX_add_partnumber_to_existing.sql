-- ============================================
-- FIX: Mevcut Kayıtlara PartNumber Ata
-- ============================================
-- Bu script mevcut DollySubmissionHold kayıtlarına
-- PartNumber atayarak Web Operator panelinde görünmesini sağlar

PRINT '🔧 Mevcut kayıtlara PartNumber atanıyor...';
PRINT '';

-- NULL PartNumber'ları kontrol et
DECLARE @NullCount INT;
SELECT @NullCount = COUNT(*)
FROM DollySubmissionHold
WHERE PartNumber IS NULL AND Status = 'pending';

PRINT 'ℹ️ NULL PartNumber sayısı: ' + CAST(@NullCount AS VARCHAR);

-- NULL olanları güncelle
IF @NullCount > 0
BEGIN
    -- CustomerReferans + EOLName + Timestamp ile PartNumber oluştur
    -- Prefix: MANUEL- (varsayılan olarak manuel toplama kabul ediliyor)
    UPDATE DollySubmissionHold
    SET PartNumber = 
        'MANUEL-' + 
        COALESCE(REPLACE(LEFT(CustomerReferans, 8), ' ', ''), 'CUST') + '-' +
        COALESCE(REPLACE(LEFT(EOLName, 8), ' ', ''), 'EOL') + '-' +
        FORMAT(COALESCE(CreatedAt, GETDATE()), 'yyyyMMddHHmmss') + '-' +
        SUBSTRING(CAST(NEWID() AS VARCHAR(36)), 1, 8)
    WHERE PartNumber IS NULL AND Status = 'pending';
    
    PRINT '✅ ' + CAST(@NullCount AS VARCHAR) + ' kayıt güncellendi';
END
ELSE
BEGIN
    PRINT '✅ Tüm kayıtlarda PartNumber mevcut';
END;

PRINT '';
PRINT '📊 Güncel Durum:';
PRINT '================';

-- Pending task'leri grupla
SELECT 
    PartNumber,
    CustomerReferans,
    EOLName,
    COUNT(*) AS 'TotalVINs',
    MIN(CreatedAt) AS 'CreatedAt',
    Status
FROM DollySubmissionHold
WHERE Status = 'pending'
GROUP BY PartNumber, CustomerReferans, EOLName, Status
ORDER BY MIN(CreatedAt) DESC;

PRINT '';
PRINT '✅ Web Operator panelinde bu task\'ler artık görünecek!';
