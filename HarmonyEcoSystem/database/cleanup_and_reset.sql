-- =====================================================
-- HarmonyEcoSystem - Verileri Temizleme ve Sıfırlama
-- Tarih: 22.11.2025
-- =====================================================

-- 1. Önce tüm işlem kayıtlarını temizle
PRINT 'Temizlik başlatılıyor...'

-- DollySubmissionHold tablosunu temizle (manuel toplama kayıtları)
IF OBJECT_ID('[ControlTower].[dbo].[DollySubmissionHold]', 'U') IS NOT NULL
BEGIN
    PRINT 'DollySubmissionHold tablosu temizleniyor...'
    DELETE FROM [ControlTower].[dbo].[DollySubmissionHold];
    DBCC CHECKIDENT ('[ControlTower].[dbo].[DollySubmissionHold]', RESEED, 0);
    PRINT 'DollySubmissionHold temizlendi.'
END

-- WebOperatorTask tablosunu temizle
IF OBJECT_ID('[ControlTower].[dbo].[WebOperatorTask]', 'U') IS NOT NULL
BEGIN
    PRINT 'WebOperatorTask tablosu temizleniyor...'
    DELETE FROM [ControlTower].[dbo].[WebOperatorTask];
    DBCC CHECKIDENT ('[ControlTower].[dbo].[WebOperatorTask]', RESEED, 0);
    PRINT 'WebOperatorTask temizlendi.'
END

-- SeferDollyEOL tablosunu temizle (sadece test kayıtları)
IF OBJECT_ID('[ControlTower].[dbo].[SeferDollyEOL]', 'U') IS NOT NULL
BEGIN
    PRINT 'SeferDollyEOL tablosu temizleniyor...'
    -- Sadece MANUEL- veya TERMINAL- başlangıçlı kayıtları sil (test kayıtları)
    DELETE FROM [ControlTower].[dbo].[SeferDollyEOL] 
    WHERE PartNumber LIKE 'MANUEL-%' OR PartNumber LIKE 'TERMINAL-%' OR PartNumber LIKE 'PT%';
    PRINT 'SeferDollyEOL test kayıtları temizlendi.'
END

-- DollyLifecycle tablosunu temizle (opsiyonel - lifecycle kayıtları)
IF OBJECT_ID('[ControlTower].[dbo].[DollyLifecycle]', 'U') IS NOT NULL
BEGIN
    PRINT 'DollyLifecycle tablosu temizleniyor...'
    DELETE FROM [ControlTower].[dbo].[DollyLifecycle];
    DBCC CHECKIDENT ('[ControlTower].[dbo].[DollyLifecycle]', RESEED, 0);
    PRINT 'DollyLifecycle temizlendi.'
END

-- AuditLog tablosunu temizle (opsiyonel - log kayıtları)
IF OBJECT_ID('[ControlTower].[dbo].[AuditLog]', 'U') IS NOT NULL
BEGIN
    PRINT 'AuditLog tablosu temizleniyor...'
    DELETE FROM [ControlTower].[dbo].[AuditLog];
    DBCC CHECKIDENT ('[ControlTower].[dbo].[AuditLog]', RESEED, 0);
    PRINT 'AuditLog temizlendi.'
END

-- 2. Kontrol sorguları - temizlik sonrası kayıt sayıları
PRINT '========================================='
PRINT 'Temizlik tamamlandı. Kayıt sayıları:'
PRINT '========================================='

SELECT 'DollySubmissionHold' AS TableName, COUNT(*) AS RecordCount 
FROM [ControlTower].[dbo].[DollySubmissionHold]
UNION ALL
SELECT 'WebOperatorTask', COUNT(*) 
FROM [ControlTower].[dbo].[WebOperatorTask]
UNION ALL
SELECT 'SeferDollyEOL (Test kayıtlar)', COUNT(*) 
FROM [ControlTower].[dbo].[SeferDollyEOL] 
WHERE PartNumber LIKE 'MANUEL-%' OR PartNumber LIKE 'TERMINAL-%' OR PartNumber LIKE 'PT%'
UNION ALL
SELECT 'DollyLifecycle', COUNT(*) 
FROM [ControlTower].[dbo].[DollyLifecycle]
UNION ALL
SELECT 'AuditLog', COUNT(*) 
FROM [ControlTower].[dbo].[AuditLog];

PRINT '========================================='
PRINT 'Temizlik işlemi başarıyla tamamlandı!'
PRINT 'Uygulama yeniden başlatılabilir.'
PRINT '========================================='

-- 3. Mevcut DollyEOLInfo verilerini kontrol et
PRINT ''
PRINT 'Mevcut DollyEOLInfo kayıtları:'
SELECT TOP 20
    DollyNo,
    VinNo,
    CustomerReferans,
    EOLName,
    EOLID,
    EOLDATE,
    Adet
FROM [ControlTower].[dbo].[DollyEOLInfo]
ORDER BY DollyNo ASC, VinNo ASC;

PRINT ''
PRINT 'Dolly bazında VIN sayıları:'
SELECT 
    DollyNo,
    COUNT(DISTINCT VinNo) AS VIN_Count,
    EOLName,
    CustomerReferans
FROM [ControlTower].[dbo].[DollyEOLInfo]
WHERE DollyNo IN ('5170427', '5170428', '5170429')
GROUP BY DollyNo, EOLName, CustomerReferans
ORDER BY DollyNo;
