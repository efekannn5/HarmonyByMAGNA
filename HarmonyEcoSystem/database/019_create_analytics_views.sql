-- ============================================================================
-- Migration: Analytics Views for Management Dashboard
-- Purpose: Create read-only views for executive analytics and reporting
-- Date: 2026-01-18
-- Impact: No impact on operational system - READ ONLY
-- ============================================================================

USE ControlTower;
GO

-- ============================================================================
-- 1. MAIN ANALYTICS VIEW - Complete Dolly Journey Tracking
-- ============================================================================
-- Purpose: Track complete lifecycle with all timestamps and duration metrics
-- Usage: Base view for all analytics queries
-- ============================================================================

IF OBJECT_ID('dbo.vw_Analytics_DollyJourney', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_DollyJourney;
GO

CREATE VIEW dbo.vw_Analytics_DollyJourney AS
SELECT 
    -- Identification
    eol.DollyNo,
    eol.VinNo,
    eol.PartNumber,
    eol.CustomerReferans,
    eol.EOLName AS ProductionLine,
    eol.EOLID AS StationID,
    
    -- Stage 1: Production (EOL)
    eol.EOLDATE AS ProductionCompletedAt,
    eol.InsertedAt AS ProductionRecordedAt,
    
    -- Stage 2: Forklift Scanning
    hold.CreatedAt AS ScanStartedAt,
    hold.LoadingCompletedAt AS LoadingCompletedAt,
    hold.TerminalUser AS ForkliftOperator,
    hold.ScanOrder AS LoadingSequence,
    hold.LoadingSessionId AS SessionID,
    
    -- Stage 3: Web Operator Processing
    hold.UpdatedAt AS WebProcessingAt,
    hold.SeferNumarasi AS ShipmentNumber,
    hold.PlakaNo AS VehiclePlate,
    
    -- Stage 4: Final Shipment
    sefer.ASNDate AS ASNSentAt,
    sefer.IrsaliyeDate AS WaybillSentAt,
    sefer.VeriGirisUser AS WebOperator,
    
    -- Duration Metrics (in minutes)
    DATEDIFF(MINUTE, eol.EOLDATE, hold.CreatedAt) AS Duration_Production_To_Scan,
    DATEDIFF(MINUTE, hold.CreatedAt, hold.LoadingCompletedAt) AS Duration_Scan_To_Loading,
    DATEDIFF(MINUTE, hold.LoadingCompletedAt, hold.UpdatedAt) AS Duration_Loading_To_WebEntry,
    DATEDIFF(MINUTE, hold.UpdatedAt, COALESCE(sefer.ASNDate, sefer.IrsaliyeDate)) AS Duration_WebEntry_To_Shipment,
    DATEDIFF(MINUTE, eol.EOLDATE, COALESCE(sefer.ASNDate, sefer.IrsaliyeDate)) AS Duration_Total,
    
    -- Status Indicators
    CASE 
        WHEN sefer.ASNDate IS NOT NULL OR sefer.IrsaliyeDate IS NOT NULL THEN 'COMPLETED'
        WHEN hold.SeferNumarasi IS NOT NULL THEN 'WEB_PROCESSING'
        WHEN hold.LoadingCompletedAt IS NOT NULL THEN 'LOADING_COMPLETED'
        WHEN hold.CreatedAt IS NOT NULL THEN 'SCANNING'
        ELSE 'PRODUCTION'
    END AS CurrentStage,
    
    -- Shipment Type
    CASE 
        WHEN sefer.ASNDate IS NOT NULL AND sefer.IrsaliyeDate IS NOT NULL THEN 'BOTH'
        WHEN sefer.ASNDate IS NOT NULL THEN 'ASN'
        WHEN sefer.IrsaliyeDate IS NOT NULL THEN 'WAYBILL'
        ELSE NULL
    END AS ShipmentType,
    
    -- Metadata
    eol.Adet AS Quantity,
    hold.Status AS HoldStatus,
    CAST(eol.EOLDATE AS DATE) AS ProductionDate,
    DATEPART(HOUR, eol.EOLDATE) AS ProductionHour,
    CASE 
        WHEN DATEPART(HOUR, eol.EOLDATE) BETWEEN 8 AND 15 THEN 'SHIFT_1'
        WHEN DATEPART(HOUR, eol.EOLDATE) BETWEEN 16 AND 23 THEN 'SHIFT_2'
        ELSE 'SHIFT_3'
    END AS ProductionShift

FROM dbo.DollyEOLInfo eol
LEFT JOIN dbo.DollySubmissionHold hold ON eol.DollyNo = hold.DollyNo AND eol.VinNo = hold.VinNo
LEFT JOIN dbo.SeferDollyEOL sefer ON eol.DollyNo = sefer.DollyNo AND eol.VinNo = sefer.VinNo
WHERE eol.EOLDATE IS NOT NULL;

GO

-- ============================================================================
-- 2. DAILY SUMMARY VIEW - Key Performance Indicators
-- ============================================================================
-- Purpose: Daily aggregated metrics for KPI dashboard cards
-- Usage: Main dashboard overview, daily trends
-- ============================================================================

IF OBJECT_ID('dbo.vw_Analytics_DailySummary', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_DailySummary;
GO

CREATE VIEW dbo.vw_Analytics_DailySummary AS
SELECT 
    ProductionDate,
    
    -- Volume Metrics
    COUNT(*) AS TotalDollys,
    COUNT(CASE WHEN CurrentStage = 'COMPLETED' THEN 1 END) AS CompletedDollys,
    COUNT(CASE WHEN CurrentStage = 'SCANNING' THEN 1 END) AS ScanningDollys,
    COUNT(CASE WHEN CurrentStage = 'LOADING_COMPLETED' THEN 1 END) AS LoadingCompletedDollys,
    COUNT(CASE WHEN CurrentStage = 'WEB_PROCESSING' THEN 1 END) AS WebProcessingDollys,
    COUNT(CASE WHEN CurrentStage = 'PRODUCTION' THEN 1 END) AS ProductionDollys,
    
    -- Performance Metrics (Average Duration in Hours)
    AVG(CAST(Duration_Production_To_Scan AS FLOAT)) / 60.0 AS AvgHours_Production_To_Scan,
    AVG(CAST(Duration_Scan_To_Loading AS FLOAT)) / 60.0 AS AvgHours_Scan_To_Loading,
    AVG(CAST(Duration_Loading_To_WebEntry AS FLOAT)) / 60.0 AS AvgHours_Loading_To_WebEntry,
    AVG(CAST(Duration_WebEntry_To_Shipment AS FLOAT)) / 60.0 AS AvgHours_WebEntry_To_Shipment,
    AVG(CAST(Duration_Total AS FLOAT)) / 60.0 AS AvgHours_Total,
    
    -- Min/Max for Range Analysis
    MIN(CAST(Duration_Total AS FLOAT)) / 60.0 AS MinHours_Total,
    MAX(CAST(Duration_Total AS FLOAT)) / 60.0 AS MaxHours_Total,
    
    -- Target Achievement (assuming 4.5 hour target)
    COUNT(CASE WHEN Duration_Total <= 270 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) AS TargetAchievementPercent,
    
    -- Shipment Type Distribution
    COUNT(CASE WHEN ShipmentType = 'ASN' THEN 1 END) AS ASN_Count,
    COUNT(CASE WHEN ShipmentType = 'WAYBILL' THEN 1 END) AS Waybill_Count,
    COUNT(CASE WHEN ShipmentType = 'BOTH' THEN 1 END) AS Both_Count

FROM dbo.vw_Analytics_DollyJourney
GROUP BY ProductionDate;

GO

-- ============================================================================
-- 3. PRODUCTION LINE PERFORMANCE VIEW
-- ============================================================================
-- Purpose: Analyze performance by production line (EOL station)
-- Usage: Line comparison, bottleneck identification
-- ============================================================================

IF OBJECT_ID('dbo.vw_Analytics_LinePerformance', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_LinePerformance;
GO

CREATE VIEW dbo.vw_Analytics_LinePerformance AS
SELECT 
    ProductionLine,
    ProductionDate,
    
    -- Volume
    COUNT(*) AS TotalDollys,
    COUNT(CASE WHEN CurrentStage = 'COMPLETED' THEN 1 END) AS CompletedDollys,
    
    -- Average Durations (in Hours)
    AVG(CAST(Duration_Production_To_Scan AS FLOAT)) / 60.0 AS AvgHours_Production_To_Scan,
    AVG(CAST(Duration_Scan_To_Loading AS FLOAT)) / 60.0 AS AvgHours_Scan_To_Loading,
    AVG(CAST(Duration_Total AS FLOAT)) / 60.0 AS AvgHours_Total,
    
    -- Performance Score (% within 4.5 hour target)
    COUNT(CASE WHEN Duration_Total <= 270 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) AS PerformanceScore,
    
    -- Efficiency Ranking (lower duration = better)
    RANK() OVER (PARTITION BY ProductionDate ORDER BY AVG(Duration_Total)) AS DailyRank,
    
    -- Part Number Diversity
    COUNT(DISTINCT PartNumber) AS UniquePartNumbers

FROM dbo.vw_Analytics_DollyJourney
WHERE ProductionLine IS NOT NULL
GROUP BY ProductionLine, ProductionDate;

GO

-- ============================================================================
-- 4. OPERATOR PERFORMANCE VIEW (ANONYMIZED)
-- ============================================================================
-- Purpose: Track operator efficiency without exposing personal identifiers
-- Usage: Performance monitoring, workload balancing
-- Note: Operators identified by hashed IDs only
-- ============================================================================

IF OBJECT_ID('dbo.vw_Analytics_OperatorPerformance', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_OperatorPerformance;
GO

CREATE VIEW dbo.vw_Analytics_OperatorPerformance AS
SELECT 
    -- Anonymized Operator Identifier
    CONVERT(VARCHAR(10), HASHBYTES('MD5', ISNULL(ForkliftOperator, 'UNKNOWN')), 2) AS OperatorID_Forklift,
    CONVERT(VARCHAR(10), HASHBYTES('MD5', ISNULL(WebOperator, 'UNKNOWN')), 2) AS OperatorID_Web,
    
    ProductionDate,
    ProductionShift,
    
    -- Forklift Metrics
    COUNT(CASE WHEN ForkliftOperator IS NOT NULL THEN 1 END) AS Forklift_ProcessedDollys,
    AVG(CASE WHEN ForkliftOperator IS NOT NULL THEN CAST(Duration_Scan_To_Loading AS FLOAT) END) / 60.0 AS Forklift_AvgHours,
    
    -- Web Operator Metrics
    COUNT(CASE WHEN WebOperator IS NOT NULL THEN 1 END) AS Web_ProcessedDollys,
    AVG(CASE WHEN WebOperator IS NOT NULL THEN CAST(Duration_WebEntry_To_Shipment AS FLOAT) END) / 60.0 AS Web_AvgHours,
    
    -- Quality Metrics (on-time completion)
    COUNT(CASE WHEN Duration_Total <= 270 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) AS OnTimePercent

FROM dbo.vw_Analytics_DollyJourney
GROUP BY 
    CONVERT(VARCHAR(10), HASHBYTES('MD5', ISNULL(ForkliftOperator, 'UNKNOWN')), 2),
    CONVERT(VARCHAR(10), HASHBYTES('MD5', ISNULL(WebOperator, 'UNKNOWN')), 2),
    ProductionDate,
    ProductionShift;

GO

-- ============================================================================
-- 5. BOTTLENECK DETECTION VIEW
-- ============================================================================
-- Purpose: Identify delayed dollys and process bottlenecks
-- Usage: Real-time alerts, problem resolution
-- ============================================================================

IF OBJECT_ID('dbo.vw_Analytics_Bottlenecks', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_Bottlenecks;
GO

CREATE VIEW dbo.vw_Analytics_Bottlenecks AS
SELECT 
    DollyNo,
    VinNo,
    PartNumber,
    ProductionLine,
    CurrentStage,
    
    -- Timestamps
    ProductionCompletedAt,
    ScanStartedAt,
    LoadingCompletedAt,
    ASNSentAt,
    
    -- Durations (in Hours)
    Duration_Production_To_Scan / 60.0 AS Hours_Production_To_Scan,
    Duration_Scan_To_Loading / 60.0 AS Hours_Scan_To_Loading,
    Duration_Loading_To_WebEntry / 60.0 AS Hours_Loading_To_WebEntry,
    Duration_WebEntry_To_Shipment / 60.0 AS Hours_WebEntry_To_Shipment,
    Duration_Total / 60.0 AS Hours_Total,
    
    -- Alert Level
    CASE 
        WHEN Duration_Total > 360 THEN 'CRITICAL'  -- > 6 hours
        WHEN Duration_Total > 300 THEN 'WARNING'   -- > 5 hours
        WHEN Duration_Total > 270 THEN 'ATTENTION' -- > 4.5 hours
        ELSE 'NORMAL'
    END AS AlertLevel,
    
    -- Bottleneck Stage Identification
    CASE 
        WHEN Duration_Production_To_Scan > 180 THEN 'FORKLIFT_DELAY'
        WHEN Duration_Scan_To_Loading > 180 THEN 'LOADING_DELAY'
        WHEN Duration_Loading_To_WebEntry > 60 THEN 'WEB_ENTRY_DELAY'
        WHEN Duration_WebEntry_To_Shipment > 30 THEN 'SHIPMENT_DELAY'
        ELSE 'NO_BOTTLENECK'
    END AS BottleneckStage,
    
    -- Current Wait Time (for incomplete dollys)
    CASE 
        WHEN CurrentStage != 'COMPLETED' THEN 
            DATEDIFF(MINUTE, ProductionCompletedAt, GETDATE()) / 60.0
        ELSE NULL
    END AS CurrentWaitHours

FROM dbo.vw_Analytics_DollyJourney
WHERE CurrentStage != 'COMPLETED' 
   OR Duration_Total > 270;  -- Include completed but over-target

GO

-- ============================================================================
-- 6. HOURLY THROUGHPUT VIEW
-- ============================================================================
-- Purpose: Track production throughput by hour for capacity planning
-- Usage: Shift analysis, peak hour identification
-- ============================================================================

IF OBJECT_ID('dbo.vw_Analytics_HourlyThroughput', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_HourlyThroughput;
GO

CREATE VIEW dbo.vw_Analytics_HourlyThroughput AS
SELECT 
    ProductionDate,
    ProductionHour,
    ProductionShift,
    
    -- Throughput Metrics
    COUNT(*) AS DollysProduced,
    COUNT(CASE WHEN CurrentStage = 'COMPLETED' THEN 1 END) AS DollysCompleted,
    COUNT(DISTINCT ProductionLine) AS ActiveLines,
    
    -- Efficiency
    AVG(CAST(Duration_Total AS FLOAT)) / 60.0 AS AvgHours_Total,
    COUNT(CASE WHEN Duration_Total <= 270 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) AS OnTimePercent,
    
    -- Part Diversity
    COUNT(DISTINCT PartNumber) AS UniquePartNumbers

FROM dbo.vw_Analytics_DollyJourney
GROUP BY ProductionDate, ProductionHour, ProductionShift;

GO

-- ============================================================================
-- 7. CUSTOMER REFERENCE ANALYSIS VIEW
-- ============================================================================
-- Purpose: Analyze performance by customer reference
-- Usage: Customer SLA monitoring, priority management
-- ============================================================================

IF OBJECT_ID('dbo.vw_Analytics_CustomerPerformance', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_CustomerPerformance;
GO

CREATE VIEW dbo.vw_Analytics_CustomerPerformance AS
SELECT 
    CustomerReferans,
    ProductionDate,
    
    -- Volume
    COUNT(*) AS TotalDollys,
    SUM(Quantity) AS TotalQuantity,
    
    -- Performance
    AVG(CAST(Duration_Total AS FLOAT)) / 60.0 AS AvgHours_Total,
    MIN(CAST(Duration_Total AS FLOAT)) / 60.0 AS MinHours_Total,
    MAX(CAST(Duration_Total AS FLOAT)) / 60.0 AS MaxHours_Total,
    
    -- Completion Status
    COUNT(CASE WHEN CurrentStage = 'COMPLETED' THEN 1 END) AS CompletedDollys,
    COUNT(CASE WHEN CurrentStage != 'COMPLETED' THEN 1 END) AS PendingDollys,
    
    -- SLA Compliance (4.5 hour target)
    COUNT(CASE WHEN Duration_Total <= 270 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) AS SLA_CompliancePercent

FROM dbo.vw_Analytics_DollyJourney
WHERE CustomerReferans IS NOT NULL
GROUP BY CustomerReferans, ProductionDate;

GO

-- ============================================================================
-- 8. MONTHLY TREND VIEW
-- ============================================================================
-- Purpose: Long-term trend analysis and forecasting
-- Usage: Executive reporting, capacity planning
-- ============================================================================

IF OBJECT_ID('dbo.vw_Analytics_MonthlyTrend', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_MonthlyTrend;
GO

CREATE VIEW dbo.vw_Analytics_MonthlyTrend AS
SELECT 
    YEAR(ProductionDate) AS ProductionYear,
    MONTH(ProductionDate) AS ProductionMonth,
    DATEFROMPARTS(YEAR(ProductionDate), MONTH(ProductionDate), 1) AS MonthStart,
    
    -- Volume Metrics
    COUNT(*) AS TotalDollys,
    COUNT(CASE WHEN CurrentStage = 'COMPLETED' THEN 1 END) AS CompletedDollys,
    COUNT(DISTINCT ProductionLine) AS ActiveLines,
    COUNT(DISTINCT PartNumber) AS UniquePartNumbers,
    COUNT(DISTINCT CustomerReferans) AS UniqueCustomers,
    
    -- Performance Metrics (in Hours)
    AVG(CAST(Duration_Production_To_Scan AS FLOAT)) / 60.0 AS AvgHours_Production_To_Scan,
    AVG(CAST(Duration_Scan_To_Loading AS FLOAT)) / 60.0 AS AvgHours_Scan_To_Loading,
    AVG(CAST(Duration_Loading_To_WebEntry AS FLOAT)) / 60.0 AS AvgHours_Loading_To_WebEntry,
    AVG(CAST(Duration_WebEntry_To_Shipment AS FLOAT)) / 60.0 AS AvgHours_WebEntry_To_Shipment,
    AVG(CAST(Duration_Total AS FLOAT)) / 60.0 AS AvgHours_Total,
    
    -- Target Achievement
    COUNT(CASE WHEN Duration_Total <= 270 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) AS TargetAchievementPercent,
    
    -- Shipment Distribution
    COUNT(CASE WHEN ShipmentType = 'ASN' THEN 1 END) AS ASN_Count,
    COUNT(CASE WHEN ShipmentType = 'WAYBILL' THEN 1 END) AS Waybill_Count,
    COUNT(CASE WHEN ShipmentType = 'BOTH' THEN 1 END) AS Both_Count

FROM dbo.vw_Analytics_DollyJourney
GROUP BY YEAR(ProductionDate), MONTH(ProductionDate);

GO

-- ============================================================================
-- 9. PART NUMBER ANALYSIS VIEW
-- ============================================================================
-- Purpose: Analyze performance and volume by part number
-- Usage: Part-specific optimization, inventory planning
-- ============================================================================

IF OBJECT_ID('dbo.vw_Analytics_PartNumberPerformance', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_PartNumberPerformance;
GO

CREATE VIEW dbo.vw_Analytics_PartNumberPerformance AS
SELECT 
    PartNumber,
    ProductionDate,
    
    -- Volume
    COUNT(*) AS TotalDollys,
    SUM(Quantity) AS TotalQuantity,
    COUNT(DISTINCT ProductionLine) AS ProductionLines,
    
    -- Performance
    AVG(CAST(Duration_Total AS FLOAT)) / 60.0 AS AvgHours_Total,
    
    -- Completion
    COUNT(CASE WHEN CurrentStage = 'COMPLETED' THEN 1 END) AS CompletedDollys,
    COUNT(CASE WHEN CurrentStage = 'COMPLETED' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) AS CompletionRate,
    
    -- Target Achievement
    COUNT(CASE WHEN Duration_Total <= 270 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) AS TargetAchievementPercent

FROM dbo.vw_Analytics_DollyJourney
WHERE PartNumber IS NOT NULL
GROUP BY PartNumber, ProductionDate;

GO

-- ============================================================================
-- 10. REAL-TIME STATUS VIEW
-- ============================================================================
-- Purpose: Current snapshot for live dashboard
-- Usage: Real-time monitoring, quick status overview
-- ============================================================================

IF OBJECT_ID('dbo.vw_Analytics_RealtimeStatus', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_RealtimeStatus;
GO

CREATE VIEW dbo.vw_Analytics_RealtimeStatus AS
SELECT 
    -- Current Stage Distribution
    CurrentStage,
    COUNT(*) AS DollyCount,
    
    -- Average Wait Time (for non-completed)
    AVG(CASE 
        WHEN CurrentStage != 'COMPLETED' 
        THEN DATEDIFF(MINUTE, ProductionCompletedAt, GETDATE()) / 60.0
        ELSE NULL
    END) AS AvgWaitHours,
    
    -- Oldest Item Wait Time
    MAX(CASE 
        WHEN CurrentStage != 'COMPLETED' 
        THEN DATEDIFF(MINUTE, ProductionCompletedAt, GETDATE()) / 60.0
        ELSE NULL
    END) AS MaxWaitHours,
    
    -- Alert Distribution
    COUNT(CASE WHEN DATEDIFF(MINUTE, ProductionCompletedAt, GETDATE()) > 360 THEN 1 END) AS CriticalAlerts,
    COUNT(CASE WHEN DATEDIFF(MINUTE, ProductionCompletedAt, GETDATE()) > 300 THEN 1 END) AS WarningAlerts

FROM dbo.vw_Analytics_DollyJourney
GROUP BY CurrentStage;

GO

-- ============================================================================
-- GRANTS AND PERMISSIONS (Optional - for read-only analytics user)
-- ============================================================================
-- Uncomment and modify for production use with dedicated analytics user account

/*
-- Create read-only analytics user
CREATE LOGIN analytics_reader WITH PASSWORD = 'SecurePassword123!';
CREATE USER analytics_reader FOR LOGIN analytics_reader;

-- Grant SELECT permissions on analytics views only
GRANT SELECT ON dbo.vw_Analytics_DollyJourney TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_DailySummary TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_LinePerformance TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_OperatorPerformance TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_Bottlenecks TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_HourlyThroughput TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_CustomerPerformance TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_MonthlyTrend TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_PartNumberPerformance TO analytics_reader;
GRANT SELECT ON dbo.vw_Analytics_RealtimeStatus TO analytics_reader;

-- DENY write permissions explicitly
DENY INSERT, UPDATE, DELETE ON SCHEMA::dbo TO analytics_reader;
*/

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify all views created successfully
SELECT 
    TABLE_NAME AS ViewName,
    'Created Successfully' AS Status
FROM INFORMATION_SCHEMA.VIEWS
WHERE TABLE_NAME LIKE 'vw_Analytics_%'
ORDER BY TABLE_NAME;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================

PRINT '-----------------------------------------------------------';
PRINT 'Analytics Views Migration Completed Successfully';
PRINT '-----------------------------------------------------------';
PRINT 'Created Views:';
PRINT '  [*] vw_Analytics_DollyJourney';
PRINT '  [*] vw_Analytics_DailySummary';
PRINT '  [*] vw_Analytics_LinePerformance';
PRINT '  [*] vw_Analytics_OperatorPerformance';
PRINT '  [*] vw_Analytics_Bottlenecks';
PRINT '  [*] vw_Analytics_HourlyThroughput';
PRINT '  [*] vw_Analytics_CustomerPerformance';
PRINT '  [*] vw_Analytics_MonthlyTrend';
PRINT '  [*] vw_Analytics_PartNumberPerformance';
PRINT '  [*] vw_Analytics_RealtimeStatus';
PRINT '-----------------------------------------------------------';
PRINT 'Note: These views are READ-ONLY and do not affect operational data';
PRINT '-----------------------------------------------------------';

GO
