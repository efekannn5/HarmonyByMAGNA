-- =====================================================
-- HARMONYVIEW - SÜRE ANALİZİ SQL VIEW'LARI (v2.4)
-- Güncelleme: 2026-02-08
-- DÜZELTME: Tüm ortalama süreleri 1 hane (DECIMAL(10,1)) ile sabitleme
-- =====================================================

-- =====================================================
-- 0. VW_DollyCompletion
-- =====================================================
IF OBJECT_ID('VW_DollyCompletion', 'V') IS NOT NULL
    DROP VIEW VW_DollyCompletion;
GO

CREATE VIEW VW_DollyCompletion AS
SELECT 
    sde.DollyNo,
    sde.SeferNumarasi,
    sde.PlakaNo,
    MAX(sde.EOLName) AS EOLName,
    MAX(sde.EOLID) AS EOLID,
    MAX(sde.PartNumber) AS PartNumber,
    COUNT(DISTINCT sde.VinNo) AS VinCount,
    MIN(dei.InsertedAt) AS IlkVinZamani,
    MAX(dei.InsertedAt) AS SonVinZamani,
    MIN(sde.TerminalDate) AS TerminalOkutmaZamani,
    MIN(sde.ASNDate) AS ASN_GonderimZamani,
    MIN(sde.IrsaliyeDate) AS Irsaliye_GonderimZamani,
    SUM(ISNULL(sde.Adet, 1)) AS ToplamAdet,
    MAX(sde.TerminalUser) AS ForkliftOperator,
    MAX(sde.VeriGirisUser) AS DataEntryOperator,
    CASE 
        WHEN MAX(sde.EOLName) LIKE 'V710-LLS%' OR MAX(sde.EOLName) LIKE 'V710-MR%' THEN 'V710 Ayna & LLS'
        WHEN MAX(sde.EOLName) LIKE 'J74-LLS%' OR MAX(sde.EOLName) LIKE 'J74-MR%' THEN 'J74 Ayna & LLS'
        WHEN MAX(sde.EOLName) LIKE '%ONTAMPON%' OR MAX(sde.EOLName) LIKE '%HLF%' OR MAX(sde.EOLName) LIKE '%BUMPER%' THEN 
            CASE 
                WHEN MAX(sde.EOLName) LIKE 'J74%' THEN 'J74 Ontampon & HLF'
                WHEN MAX(sde.EOLName) LIKE 'V710%' THEN 'V710 Ontampon'
                ELSE 'Ontampon Diğer'
            END
        WHEN MAX(sde.EOLName) LIKE '%HEADLAMP%' OR MAX(sde.EOLName) LIKE '%FINISHER%' THEN 'Headlamp Finisher'
        ELSE 'Diğer'
    END AS GroupName
FROM SeferDollyEOL sde WITH (NOLOCK)
LEFT JOIN DollyEOLInfo dei WITH (NOLOCK) 
    ON sde.DollyNo = dei.DollyNo 
    AND sde.VinNo = dei.VinNo
WHERE sde.SeferNumarasi IS NOT NULL
GROUP BY sde.DollyNo, sde.SeferNumarasi, sde.PlakaNo;
GO

-- =====================================================
-- 1. VW_DollyProcessTimeline
-- =====================================================
IF OBJECT_ID('VW_DollyProcessTimeline', 'V') IS NOT NULL
    DROP VIEW VW_DollyProcessTimeline;
GO

CREATE VIEW VW_DollyProcessTimeline AS
SELECT 
    DollyNo,
    SeferNumarasi,
    PlakaNo,
    EOLName,
    PartNumber,
    EOLID,
    GroupName,
    VinCount,
    ToplamAdet AS Adet,
    ForkliftOperator,
    DataEntryOperator,
    IlkVinZamani AS EOL_CikisZamani,
    SonVinZamani AS DollyHazirZamani,
    TerminalOkutmaZamani AS TerminalDate,
    ASN_GonderimZamani AS ASNDate,
    COALESCE(ASN_GonderimZamani, Irsaliye_GonderimZamani) AS DocDate,
    ISNULL(DATEDIFF(MINUTE, IlkVinZamani, SonVinZamani), 0) AS DollyDoldurmaSuresi_Min,
    CASE WHEN SonVinZamani IS NOT NULL AND TerminalOkutmaZamani IS NOT NULL 
         THEN DATEDIFF(MINUTE, SonVinZamani, TerminalOkutmaZamani) ELSE 15 END AS EOL_To_Terminal_Min,
    CASE WHEN TerminalOkutmaZamani IS NOT NULL AND ASN_GonderimZamani IS NOT NULL 
         THEN DATEDIFF(MINUTE, TerminalOkutmaZamani, ASN_GonderimZamani) ELSE 10 END AS Terminal_To_ASN_Min,
    CASE 
        WHEN SonVinZamani IS NOT NULL AND (ASN_GonderimZamani IS NOT NULL OR Irsaliye_GonderimZamani IS NOT NULL) 
        THEN DATEDIFF(MINUTE, SonVinZamani, COALESCE(ASN_GonderimZamani, Irsaliye_GonderimZamani))
        WHEN TerminalOkutmaZamani IS NOT NULL AND (ASN_GonderimZamani IS NOT NULL OR Irsaliye_GonderimZamani IS NOT NULL)
        THEN DATEDIFF(MINUTE, TerminalOkutmaZamani, COALESCE(ASN_GonderimZamani, Irsaliye_GonderimZamani)) + 15
        ELSE NULL
    END AS ToplamSure_Min,
    CAST(COALESCE(ASN_GonderimZamani, Irsaliye_GonderimZamani) AS DATE) AS IslemTarihi,
    CASE 
        WHEN CAST(COALESCE(ASN_GonderimZamani, Irsaliye_GonderimZamani) AS TIME) < '08:00:00' THEN 1
        WHEN CAST(COALESCE(ASN_GonderimZamani, Irsaliye_GonderimZamani) AS TIME) >= '08:00:00' AND CAST(COALESCE(ASN_GonderimZamani, Irsaliye_GonderimZamani) AS TIME) < '16:00:00' THEN 2
        ELSE 3
    END AS Vardiya
FROM VW_DollyCompletion
WHERE COALESCE(ASN_GonderimZamani, Irsaliye_GonderimZamani) IS NOT NULL;
GO

-- =====================================================
-- 2. VW_SeferSummary
-- =====================================================
IF OBJECT_ID('VW_SeferSummary', 'V') IS NOT NULL
    DROP VIEW VW_SeferSummary;
GO

CREATE VIEW VW_SeferSummary AS
SELECT 
    SeferNumarasi,
    PlakaNo,
    MAX(ForkliftOperator) AS ForkliftOperator,
    MAX(DataEntryOperator) AS DataEntryOperator,
    COUNT(DISTINCT DollyNo) AS ToplamDolly,
    SUM(VinCount) AS ToplamVIN,
    SUM(Adet) AS ToplamAdet,
    MIN(TerminalDate) AS IlkOkutma,
    MAX(TerminalDate) AS SonOkutma,
    MAX(DocDate) AS DocDate,
    CAST(AVG(CASE WHEN ToplamSure_Min > 0 THEN CAST(ToplamSure_Min AS FLOAT) ELSE NULL END) AS DECIMAL(10,1)) AS ToplamSure_Min,
    DATEDIFF(MINUTE, MIN(TerminalDate), MAX(TerminalDate)) AS OkutmaSuresi_Min,
    CAST(AVG(CAST(EOL_To_Terminal_Min AS FLOAT)) AS DECIMAL(10,1)) AS BeklemeSuresi_Min,
    MAX(IslemTarihi) AS IslemTarihi,
    MAX(Vardiya) AS Vardiya
FROM VW_DollyProcessTimeline
GROUP BY SeferNumarasi, PlakaNo;
GO

-- =====================================================
-- 3. VW_DailySummary
-- =====================================================
IF OBJECT_ID('VW_DailySummary', 'V') IS NOT NULL
    DROP VIEW VW_DailySummary;
GO

CREATE VIEW VW_DailySummary AS
SELECT 
    IslemTarihi,
    Vardiya,
    COUNT(DISTINCT SeferNumarasi) AS ToplamSefer,
    COUNT(DISTINCT DollyNo) AS ToplamDolly,
    SUM(VinCount) AS ToplamVIN,
    SUM(Adet) AS ToplamAdet,
    CAST(AVG(CAST(ToplamSure_Min AS FLOAT)) AS DECIMAL(10,1)) AS OrtToplamSure_Min,
    MIN(ToplamSure_Min) AS EnHizliSure_Min,
    MAX(ToplamSure_Min) AS EnYavasSure_Min
FROM VW_DollyProcessTimeline
WHERE IslemTarihi IS NOT NULL
GROUP BY IslemTarihi, Vardiya;
GO

-- =====================================================
-- 4. VW_GroupPerformance
-- =====================================================
IF OBJECT_ID('VW_GroupPerformance', 'V') IS NOT NULL
    DROP VIEW VW_GroupPerformance;
GO

CREATE VIEW VW_GroupPerformance AS
SELECT 
    GroupName,
    COUNT(DISTINCT DollyNo) AS DollyCount,
    SUM(VinCount) AS VinCount,
    SUM(Adet) AS TotalAdet,
    CAST(AVG(CAST(ToplamSure_Min AS FLOAT)) AS DECIMAL(10,1)) AS AvgDuration_Min,
    MIN(ToplamSure_Min) AS MinDuration_Min,
    MAX(ToplamSure_Min) AS MaxDuration_Min,
    -- Backend aliases
    SUM(Adet) as total_adet,
    CAST(AVG(CAST(ToplamSure_Min AS FLOAT)) AS DECIMAL(10,1)) as avg_duration_min,
    MIN(ToplamSure_Min) as min_duration_min,
    MAX(ToplamSure_Min) as max_duration_min
FROM VW_DollyProcessTimeline
GROUP BY GroupName;
GO

-- =====================================================
-- 5. VW_OperatorPerformance
-- =====================================================
IF OBJECT_ID('VW_OperatorPerformance', 'V') IS NOT NULL
    DROP VIEW VW_OperatorPerformance;
GO

CREATE VIEW VW_OperatorPerformance AS
SELECT 
    ForkliftOperator,
    COUNT(DISTINCT SeferNumarasi) AS ToplamSefer,
    COUNT(DISTINCT DollyNo) AS ToplamDolly,
    SUM(Adet) AS ToplamAdet,
    CAST(AVG(CAST(ToplamSure_Min AS FLOAT)) AS DECIMAL(10,1)) AS OrtToplamSure_Min,
    MIN(ToplamSure_Min) AS EnHizliSure_Min,
    MAX(ToplamSure_Min) AS EnYavasSure_Min
FROM VW_DollyProcessTimeline
WHERE ForkliftOperator IS NOT NULL
GROUP BY ForkliftOperator;
GO

-- =====================================================
-- 6. VW_PartPerformance
-- =====================================================
IF OBJECT_ID('VW_PartPerformance', 'V') IS NOT NULL
    DROP VIEW VW_PartPerformance;
GO

CREATE VIEW VW_PartPerformance AS
SELECT 
    PartNumber,
    MAX(GroupName) AS GroupName,
    MAX(EOLName) AS EOLName,
    COUNT(DISTINCT DollyNo) AS ToplamDolly,
    COUNT(DISTINCT SeferNumarasi) AS ToplamSefer,
    SUM(VinCount) AS ToplamVIN,
    SUM(Adet) AS ToplamAdet,
    CAST(AVG(CAST(ToplamSure_Min AS FLOAT)) AS DECIMAL(10,1)) AS OrtSure_Min,
    MIN(ToplamSure_Min) AS MinSure_Min,
    MAX(ToplamSure_Min) AS MaxSure_Min,
    MAX(IslemTarihi) AS SonIslemTarihi
FROM VW_DollyProcessTimeline
WHERE PartNumber IS NOT NULL 
GROUP BY PartNumber;
GO

-- =====================================================
-- 7. VW_DataEntryPerformance
-- =====================================================
IF OBJECT_ID('VW_DataEntryPerformance', 'V') IS NOT NULL
    DROP VIEW VW_DataEntryPerformance;
GO

CREATE VIEW VW_DataEntryPerformance AS
SELECT 
    DataEntryOperator,
    COUNT(DISTINCT SeferNumarasi) AS ToplamSefer,
    COUNT(DISTINCT DollyNo) AS ToplamDolly,
    SUM(Adet) AS ToplamAdet,
    CAST(AVG(CAST(Terminal_To_ASN_Min AS FLOAT)) AS DECIMAL(10,1)) AS OrtVeriGirisci_Min,
    MIN(Terminal_To_ASN_Min) AS MinVeriGirisci_Min,
    MAX(Terminal_To_ASN_Min) AS MaxVeriGirisci_Min,
    MAX(IslemTarihi) AS SonIslemTarihi
FROM VW_DollyProcessTimeline
WHERE DataEntryOperator IS NOT NULL
GROUP BY DataEntryOperator;
GO

-- =====================================================
-- 8. VW_HourlyThroughput
-- =====================================================
IF OBJECT_ID('VW_HourlyThroughput', 'V') IS NOT NULL
    DROP VIEW VW_HourlyThroughput;
GO

CREATE VIEW VW_HourlyThroughput AS
SELECT 
    CAST(COALESCE(ASNDate, IrsaliyeDate) AS DATE) AS Tarih,
    DATEPART(HOUR, COALESCE(ASNDate, IrsaliyeDate)) AS Saat,
    EOLName,
    CASE 
        WHEN CAST(COALESCE(ASNDate, IrsaliyeDate) AS TIME) < '08:00:00' THEN 1
        WHEN CAST(COALESCE(ASNDate, IrsaliyeDate) AS TIME) >= '08:00:00' AND CAST(COALESCE(ASNDate, IrsaliyeDate) AS TIME) < '16:00:00' THEN 2
        ELSE 3
    END AS Vardiya,
    COUNT(DISTINCT SeferNumarasi) AS SeferSayisi,
    COUNT(DISTINCT DollyNo) AS DollySayisi,
    COUNT(*) AS VINSayisi,
    SUM(ISNULL(Adet, 1)) AS ToplamAdet
FROM SeferDollyEOL WITH (NOLOCK)
WHERE COALESCE(ASNDate, IrsaliyeDate) IS NOT NULL
GROUP BY 
    CAST(COALESCE(ASNDate, IrsaliyeDate) AS DATE), 
    DATEPART(HOUR, COALESCE(ASNDate, IrsaliyeDate)), 
    CASE 
        WHEN CAST(COALESCE(ASNDate, IrsaliyeDate) AS TIME) < '08:00:00' THEN 1
        WHEN CAST(COALESCE(ASNDate, IrsaliyeDate) AS TIME) >= '08:00:00' AND CAST(COALESCE(ASNDate, IrsaliyeDate) AS TIME) < '16:00:00' THEN 2
        ELSE 3
    END,
    EOLName;
GO
