-- ============================================================================
-- Migration: Detailed Analytics Views (Timeline + Performance)
-- Purpose : Read-only views for full end-to-end timeline and KPI reporting
-- TZ      : Assumes stored timestamps are UTC; converts to Turkey time
-- Date    : 2026-01-30
-- ============================================================================

USE ControlTower;
GO

-- ============================================================================
-- 0) Helper note: AT TIME ZONE requires SQL Server 2016+
-- ============================================================================

-- ============================================================================
-- 1) DOLLY TIMELINE (DETAILED) - one row per DollyNo + VinNo
-- ============================================================================
IF OBJECT_ID('dbo.vw_Analytics_DollyTimelineDetailed', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_DollyTimelineDetailed;
GO

CREATE VIEW dbo.vw_Analytics_DollyTimelineDetailed AS
WITH hold_agg AS (
    SELECT
        h.DollyNo,
        h.VinNo,
        MIN(h.CreatedAt) AS FirstScanAtUtc,
        MAX(h.CreatedAt) AS LastScanAtUtc,
        MAX(h.LoadingCompletedAt) AS LoadingCompletedAtUtc,
        MAX(h.UpdatedAt) AS HoldUpdatedAtUtc,
        MAX(h.SubmittedAt) AS HoldSubmittedAtUtc,
        MAX(h.SeferNumarasi) AS SeferNumarasi,
        MAX(h.PlakaNo) AS PlakaNo,
        MAX(h.TerminalUser) AS ForkliftOperator,
        MAX(h.PartNumber) AS PartNumber,
        MAX(h.CustomerReferans) AS CustomerReferans,
        MAX(h.EOLName) AS EOLName,
        MAX(h.EOLID) AS EOLID,
        MAX(h.DollyOrderNo) AS DollyOrderNo,
        MAX(h.Adet) AS Adet,
        MAX(h.LoadingSessionId) AS LoadingSessionId,
        MAX(h.ScanOrder) AS ScanOrder,
        MAX(h.Status) AS HoldStatus
    FROM dbo.DollySubmissionHold h
    GROUP BY h.DollyNo, h.VinNo
),
sefer_agg AS (
    SELECT
        s.DollyNo,
        s.VinNo,
        MAX(s.ASNDate) AS ASNSentAtUtc,
        MAX(s.IrsaliyeDate) AS IrsaliyeSentAtUtc,
        MAX(s.SeferNumarasi) AS SeferNumarasi,
        MAX(s.PlakaNo) AS PlakaNo,
        MAX(s.VeriGirisUser) AS WebOperator,
        MAX(s.TerminalDate) AS ShipmentTerminalAtUtc,
        MAX(s.PartNumber) AS PartNumber,
        MAX(s.CustomerReferans) AS CustomerReferans,
        MAX(s.EOLName) AS EOLName,
        MAX(s.EOLID) AS EOLID,
        MAX(s.DollyOrderNo) AS DollyOrderNo,
        MAX(s.Adet) AS Adet
    FROM dbo.SeferDollyEOL s
    GROUP BY s.DollyNo, s.VinNo
),
life_last AS (
    SELECT DollyNo, VinNo, Status AS LastLifecycleStatus, CreatedAt AS LastLifecycleAtUtc
    FROM (
        SELECT
            l.DollyNo,
            l.VinNo,
            l.Status,
            l.CreatedAt,
            ROW_NUMBER() OVER (PARTITION BY l.DollyNo, l.VinNo ORDER BY l.CreatedAt DESC) AS rn
        FROM dbo.DollyLifecycle l
    ) x
    WHERE x.rn = 1
),
life_first AS (
    SELECT DollyNo, VinNo, Status AS FirstLifecycleStatus, CreatedAt AS FirstLifecycleAtUtc
    FROM (
        SELECT
            l.DollyNo,
            l.VinNo,
            l.Status,
            l.CreatedAt,
            ROW_NUMBER() OVER (PARTITION BY l.DollyNo, l.VinNo ORDER BY l.CreatedAt ASC) AS rn
        FROM dbo.DollyLifecycle l
    ) x
    WHERE x.rn = 1
)
SELECT
    e.DollyNo,
    e.VinNo,
    COALESCE(h.DollyOrderNo, s.DollyOrderNo, e.DollyOrderNo) AS DollyOrderNo,
    COALESCE(h.PartNumber, s.PartNumber) AS PartNumber,
    COALESCE(h.CustomerReferans, s.CustomerReferans, e.CustomerReferans) AS CustomerReferans,
    COALESCE(h.Adet, s.Adet, e.Adet) AS Quantity,
    COALESCE(h.EOLName, s.EOLName, e.EOLName) AS EOLName,
    COALESCE(h.EOLID, s.EOLID, e.EOLID) AS EOLID,
    gm.GroupId,
    gm.GroupName,
    gm.ShippingTag,

    h.LoadingSessionId,
    h.ScanOrder,
    h.HoldStatus,
    h.ForkliftOperator,
    s.WebOperator,

    COALESCE(h.SeferNumarasi, s.SeferNumarasi) AS SeferNumarasi,
    COALESCE(h.PlakaNo, s.PlakaNo) AS PlakaNo,

    -- Task info (PartNumber based)
    t.Status AS TaskStatus,
    t.AssignedTo AS TaskAssignedToUserId,
    t.CreatedAt AS TaskCreatedAtUtc,
    t.CompletedAt AS TaskCompletedAtUtc,

    -- Raw UTC timestamps
    CAST(e.EOLDATE AS datetime2) AS ProductionCompletedAtUtc,
    e.InsertedAt AS ProductionRecordedAtUtc,
    h.FirstScanAtUtc,
    h.LastScanAtUtc,
    h.LoadingCompletedAtUtc,
    h.HoldUpdatedAtUtc,
    h.HoldSubmittedAtUtc,
    s.ShipmentTerminalAtUtc,
    s.ASNSentAtUtc,
    s.IrsaliyeSentAtUtc,
    lf.FirstLifecycleAtUtc,
    ll.LastLifecycleAtUtc,

    -- Local time (Turkey)
    ((CAST(e.EOLDATE AS datetime2)) AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS ProductionCompletedAtLocal,
    (e.InsertedAt AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS ProductionRecordedAtLocal,
    (h.FirstScanAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS FirstScanAtLocal,
    (h.LastScanAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS LastScanAtLocal,
    (h.LoadingCompletedAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS LoadingCompletedAtLocal,
    (h.HoldUpdatedAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS HoldUpdatedAtLocal,
    (h.HoldSubmittedAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS HoldSubmittedAtLocal,
    (s.ShipmentTerminalAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS ShipmentTerminalAtLocal,
    (s.ASNSentAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS ASNSentAtLocal,
    (s.IrsaliyeSentAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS IrsaliyeSentAtLocal,
    (lf.FirstLifecycleAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS FirstLifecycleAtLocal,
    (ll.LastLifecycleAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS LastLifecycleAtLocal,

    -- Lifecycle status
    lf.FirstLifecycleStatus,
    ll.LastLifecycleStatus,

    -- Current stage
    CASE
        WHEN s.ASNSentAtUtc IS NOT NULL OR s.IrsaliyeSentAtUtc IS NOT NULL THEN 'COMPLETED'
        WHEN h.HoldSubmittedAtUtc IS NOT NULL THEN 'SUBMITTED'
        WHEN h.LoadingCompletedAtUtc IS NOT NULL THEN 'LOADING_COMPLETED'
        WHEN h.FirstScanAtUtc IS NOT NULL THEN 'SCANNED'
        WHEN e.EOLDATE IS NOT NULL THEN 'PRODUCTION'
        ELSE 'UNKNOWN'
    END AS CurrentStage,

    -- Duration metrics (minutes)
    CASE WHEN e.EOLDATE IS NOT NULL AND h.FirstScanAtUtc IS NOT NULL
         THEN DATEDIFF(MINUTE, CAST(e.EOLDATE AS datetime2), h.FirstScanAtUtc) END AS Min_Production_To_FirstScan,
    CASE WHEN h.FirstScanAtUtc IS NOT NULL AND h.LoadingCompletedAtUtc IS NOT NULL
         THEN DATEDIFF(MINUTE, h.FirstScanAtUtc, h.LoadingCompletedAtUtc) END AS Min_FirstScan_To_LoadingCompleted,
    CASE WHEN h.LoadingCompletedAtUtc IS NOT NULL AND t.CreatedAt IS NOT NULL
         THEN DATEDIFF(MINUTE, h.LoadingCompletedAtUtc, t.CreatedAt) END AS Min_LoadingCompleted_To_TaskCreated,
    CASE WHEN t.CreatedAt IS NOT NULL AND COALESCE(s.ASNSentAtUtc, s.IrsaliyeSentAtUtc) IS NOT NULL
         THEN DATEDIFF(MINUTE, t.CreatedAt, COALESCE(s.ASNSentAtUtc, s.IrsaliyeSentAtUtc)) END AS Min_TaskCreated_To_Shipment,
    CASE WHEN h.FirstScanAtUtc IS NOT NULL AND COALESCE(s.ASNSentAtUtc, s.IrsaliyeSentAtUtc) IS NOT NULL
         THEN DATEDIFF(MINUTE, h.FirstScanAtUtc, COALESCE(s.ASNSentAtUtc, s.IrsaliyeSentAtUtc)) END AS Min_Scan_To_Shipment,
    CASE WHEN e.EOLDATE IS NOT NULL AND COALESCE(s.ASNSentAtUtc, s.IrsaliyeSentAtUtc) IS NOT NULL
         THEN DATEDIFF(MINUTE, CAST(e.EOLDATE AS datetime2), COALESCE(s.ASNSentAtUtc, s.IrsaliyeSentAtUtc)) END AS Min_Production_To_Shipment

FROM dbo.DollyEOLInfo e
LEFT JOIN hold_agg h ON e.DollyNo = h.DollyNo AND e.VinNo = h.VinNo
LEFT JOIN sefer_agg s ON e.DollyNo = s.DollyNo AND e.VinNo = s.VinNo
LEFT JOIN life_first lf ON e.DollyNo = lf.DollyNo AND e.VinNo = lf.VinNo
LEFT JOIN life_last ll ON e.DollyNo = ll.DollyNo AND e.VinNo = ll.VinNo
LEFT JOIN dbo.WebOperatorTask t ON t.PartNumber = COALESCE(h.PartNumber, s.PartNumber)
OUTER APPLY (
    SELECT TOP 1
        g.Id AS GroupId,
        g.GroupName,
        ge.ShippingTag
    FROM dbo.PWorkStation p
    JOIN dbo.DollyGroupEOL ge ON ge.PWorkStationId = p.Id
    JOIN dbo.DollyGroup g ON g.Id = ge.GroupId
    WHERE p.PWorkStationName = COALESCE(h.EOLName, s.EOLName, e.EOLName)
    ORDER BY ge.CreatedAt DESC
) gm;

GO

-- ============================================================================
-- 2) EVENT TIMELINE (DETAILED) - one row per event
-- ============================================================================
IF OBJECT_ID('dbo.vw_Analytics_EventTimeline', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_EventTimeline;
GO

CREATE VIEW dbo.vw_Analytics_EventTimeline AS
SELECT
    'EOL_COMPLETED' AS EventType,
    CAST(e.EOLDATE AS datetime2) AS EventTimeUtc,
    ((CAST(e.EOLDATE AS datetime2)) AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS EventTimeLocal,
    e.DollyNo,
    e.VinNo,
    e.DollyOrderNo,
    NULL AS PartNumber,
    e.CustomerReferans,
    e.EOLName,
    e.EOLID,
    NULL AS GroupName,
    NULL AS ShippingTag,
    NULL AS OperatorName,
    NULL AS SessionId,
    NULL AS SeferNumarasi,
    NULL AS PlakaNo,
    'DollyEOLInfo' AS SourceTable
FROM dbo.DollyEOLInfo e
WHERE e.EOLDATE IS NOT NULL

UNION ALL

SELECT
    'EOL_RECORDED' AS EventType,
    e.InsertedAt AS EventTimeUtc,
    (e.InsertedAt AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS EventTimeLocal,
    e.DollyNo,
    e.VinNo,
    e.DollyOrderNo,
    NULL AS PartNumber,
    e.CustomerReferans,
    e.EOLName,
    e.EOLID,
    NULL AS GroupName,
    NULL AS ShippingTag,
    NULL AS OperatorName,
    NULL AS SessionId,
    NULL AS SeferNumarasi,
    NULL AS PlakaNo,
    'DollyEOLInfo' AS SourceTable
FROM dbo.DollyEOLInfo e
WHERE e.InsertedAt IS NOT NULL

UNION ALL

SELECT
    'SCAN' AS EventType,
    h.CreatedAt AS EventTimeUtc,
    (h.CreatedAt AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS EventTimeLocal,
    h.DollyNo,
    h.VinNo,
    h.DollyOrderNo,
    h.PartNumber,
    h.CustomerReferans,
    h.EOLName,
    h.EOLID,
    NULL AS GroupName,
    NULL AS ShippingTag,
    h.TerminalUser AS OperatorName,
    h.LoadingSessionId AS SessionId,
    h.SeferNumarasi,
    h.PlakaNo,
    'DollySubmissionHold' AS SourceTable
FROM dbo.DollySubmissionHold h
WHERE h.CreatedAt IS NOT NULL

UNION ALL

SELECT
    'LOADING_COMPLETED' AS EventType,
    h.LoadingCompletedAt AS EventTimeUtc,
    (h.LoadingCompletedAt AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS EventTimeLocal,
    h.DollyNo,
    h.VinNo,
    h.DollyOrderNo,
    h.PartNumber,
    h.CustomerReferans,
    h.EOLName,
    h.EOLID,
    NULL AS GroupName,
    NULL AS ShippingTag,
    h.TerminalUser AS OperatorName,
    h.LoadingSessionId AS SessionId,
    h.SeferNumarasi,
    h.PlakaNo,
    'DollySubmissionHold' AS SourceTable
FROM dbo.DollySubmissionHold h
WHERE h.LoadingCompletedAt IS NOT NULL

UNION ALL

SELECT
    'HOLD_SUBMITTED' AS EventType,
    h.SubmittedAt AS EventTimeUtc,
    (h.SubmittedAt AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS EventTimeLocal,
    h.DollyNo,
    h.VinNo,
    h.DollyOrderNo,
    h.PartNumber,
    h.CustomerReferans,
    h.EOLName,
    h.EOLID,
    NULL AS GroupName,
    NULL AS ShippingTag,
    h.TerminalUser AS OperatorName,
    h.LoadingSessionId AS SessionId,
    h.SeferNumarasi,
    h.PlakaNo,
    'DollySubmissionHold' AS SourceTable
FROM dbo.DollySubmissionHold h
WHERE h.SubmittedAt IS NOT NULL

UNION ALL

SELECT
    'TASK_CREATED' AS EventType,
    t.CreatedAt AS EventTimeUtc,
    (t.CreatedAt AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS EventTimeLocal,
    NULL AS DollyNo,
    NULL AS VinNo,
    NULL AS DollyOrderNo,
    t.PartNumber,
    NULL AS CustomerReferans,
    NULL AS EOLName,
    NULL AS EOLID,
    NULL AS GroupName,
    t.GroupTag AS ShippingTag,
    NULL AS OperatorName,
    NULL AS SessionId,
    NULL AS SeferNumarasi,
    NULL AS PlakaNo,
    'WebOperatorTask' AS SourceTable
FROM dbo.WebOperatorTask t
WHERE t.CreatedAt IS NOT NULL

UNION ALL

SELECT
    'TASK_COMPLETED' AS EventType,
    t.CompletedAt AS EventTimeUtc,
    (t.CompletedAt AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS EventTimeLocal,
    NULL AS DollyNo,
    NULL AS VinNo,
    NULL AS DollyOrderNo,
    t.PartNumber,
    NULL AS CustomerReferans,
    NULL AS EOLName,
    NULL AS EOLID,
    NULL AS GroupName,
    t.GroupTag AS ShippingTag,
    NULL AS OperatorName,
    NULL AS SessionId,
    NULL AS SeferNumarasi,
    NULL AS PlakaNo,
    'WebOperatorTask' AS SourceTable
FROM dbo.WebOperatorTask t
WHERE t.CompletedAt IS NOT NULL

UNION ALL

SELECT
    'ASN_SENT' AS EventType,
    s.ASNDate AS EventTimeUtc,
    (s.ASNDate AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS EventTimeLocal,
    s.DollyNo,
    s.VinNo,
    s.DollyOrderNo,
    s.PartNumber,
    s.CustomerReferans,
    s.EOLName,
    s.EOLID,
    NULL AS GroupName,
    'asn' AS ShippingTag,
    s.VeriGirisUser AS OperatorName,
    NULL AS SessionId,
    s.SeferNumarasi,
    s.PlakaNo,
    'SeferDollyEOL' AS SourceTable
FROM dbo.SeferDollyEOL s
WHERE s.ASNDate IS NOT NULL

UNION ALL

SELECT
    'IRSALIYE_SENT' AS EventType,
    s.IrsaliyeDate AS EventTimeUtc,
    (s.IrsaliyeDate AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS EventTimeLocal,
    s.DollyNo,
    s.VinNo,
    s.DollyOrderNo,
    s.PartNumber,
    s.CustomerReferans,
    s.EOLName,
    s.EOLID,
    NULL AS GroupName,
    'irsaliye' AS ShippingTag,
    s.VeriGirisUser AS OperatorName,
    NULL AS SessionId,
    s.SeferNumarasi,
    s.PlakaNo,
    'SeferDollyEOL' AS SourceTable
FROM dbo.SeferDollyEOL s
WHERE s.IrsaliyeDate IS NOT NULL

UNION ALL

SELECT
    CONCAT('LIFECYCLE_', l.Status) AS EventType,
    l.CreatedAt AS EventTimeUtc,
    (l.CreatedAt AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS EventTimeLocal,
    l.DollyNo,
    l.VinNo,
    NULL AS DollyOrderNo,
    NULL AS PartNumber,
    NULL AS CustomerReferans,
    NULL AS EOLName,
    NULL AS EOLID,
    NULL AS GroupName,
    NULL AS ShippingTag,
    l.Source AS OperatorName,
    NULL AS SessionId,
    NULL AS SeferNumarasi,
    NULL AS PlakaNo,
    'DollyLifecycle' AS SourceTable
FROM dbo.DollyLifecycle l
WHERE l.CreatedAt IS NOT NULL;

GO

-- ============================================================================
-- 3) LOADING SESSION TIMELINE
-- ============================================================================
IF OBJECT_ID('dbo.vw_Analytics_LoadingSessionTimeline', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_LoadingSessionTimeline;
GO

CREATE VIEW dbo.vw_Analytics_LoadingSessionTimeline AS
SELECT
    h.LoadingSessionId,
    h.TerminalUser AS ForkliftOperator,
    MIN(h.CreatedAt) AS FirstScanAtUtc,
    MAX(h.CreatedAt) AS LastScanAtUtc,
    MAX(h.LoadingCompletedAt) AS LoadingCompletedAtUtc,
    COUNT(DISTINCT h.DollyNo) AS DollyCount,
    COUNT(*) AS VinCount,
    MIN(h.ScanOrder) AS FirstScanOrder,
    MAX(h.ScanOrder) AS LastScanOrder,
    DATEDIFF(SECOND, MIN(h.CreatedAt), MAX(h.CreatedAt)) AS Sec_ScanningDuration,
    CASE WHEN MAX(h.LoadingCompletedAt) IS NOT NULL
         THEN DATEDIFF(SECOND, MIN(h.CreatedAt), MAX(h.LoadingCompletedAt)) END AS Sec_ScanToLoadingCompleted,

    -- Local time
    (MIN(h.CreatedAt) AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS FirstScanAtLocal,
    (MAX(h.CreatedAt) AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS LastScanAtLocal,
    (MAX(h.LoadingCompletedAt) AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS LoadingCompletedAtLocal

FROM dbo.DollySubmissionHold h
WHERE h.LoadingSessionId IS NOT NULL
GROUP BY h.LoadingSessionId, h.TerminalUser;

GO

-- ============================================================================
-- 4) SCAN INTERVALS (per session)
-- ============================================================================
IF OBJECT_ID('dbo.vw_Analytics_ScanIntervals', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_ScanIntervals;
GO

CREATE VIEW dbo.vw_Analytics_ScanIntervals AS
WITH scans AS (
    SELECT
        h.LoadingSessionId,
        h.TerminalUser,
        h.DollyNo,
        h.VinNo,
        h.ScanOrder,
        h.CreatedAt AS ScanAtUtc,
        LAG(h.CreatedAt) OVER (PARTITION BY h.LoadingSessionId ORDER BY h.CreatedAt) AS PrevScanAtUtc
    FROM dbo.DollySubmissionHold h
    WHERE h.LoadingSessionId IS NOT NULL
)
SELECT
    LoadingSessionId,
    TerminalUser,
    DollyNo,
    VinNo,
    ScanOrder,
    ScanAtUtc,
    (ScanAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS ScanAtLocal,
    PrevScanAtUtc,
    (PrevScanAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS PrevScanAtLocal,
    CASE WHEN PrevScanAtUtc IS NOT NULL
         THEN DATEDIFF(SECOND, PrevScanAtUtc, ScanAtUtc) END AS Sec_SincePrevScan
FROM scans;

GO

-- ============================================================================
-- 5) FORKLIFT PERFORMANCE (daily + shift + part)
-- NOTE: DollySubmissionHold rows can be deleted after ASN send. To avoid
--       losing forklift scan history, we use DollyLifecycle SCAN_CAPTURED.
-- ============================================================================
IF OBJECT_ID('dbo.vw_Analytics_ForkliftPerformanceDaily', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_ForkliftPerformanceDaily;
GO

CREATE VIEW dbo.vw_Analytics_ForkliftPerformanceDaily AS
WITH scan_events AS (
    SELECT
        l.DollyNo,
        l.VinNo,
        CASE WHEN ISJSON(l.Metadata) = 1 THEN JSON_VALUE(l.Metadata, '$.forkliftUser') END AS ForkliftOperator,
        l.CreatedAt AS ScanAtUtc
    FROM dbo.DollyLifecycle l
    WHERE l.Status = 'SCAN_CAPTURED'
      AND l.Source = 'FORKLIFT'
),
hold_agg AS (
    SELECT
        h.DollyNo,
        h.VinNo,
        MAX(h.LoadingCompletedAt) AS LoadingCompletedAtUtc,
        MAX(h.PartNumber) AS PartNumber,
        MAX(h.EOLName) AS EOLName
    FROM dbo.DollySubmissionHold h
    GROUP BY h.DollyNo, h.VinNo
),
sefer_agg AS (
    SELECT
        s.DollyNo,
        s.VinNo,
        MAX(s.ASNDate) AS ASNSentAtUtc,
        MAX(s.IrsaliyeDate) AS IrsaliyeSentAtUtc,
        MAX(s.PartNumber) AS PartNumber,
        MAX(s.EOLName) AS EOLName
    FROM dbo.SeferDollyEOL s
    GROUP BY s.DollyNo, s.VinNo
)
SELECT
    se.ForkliftOperator,
    COALESCE(h.PartNumber, sf.PartNumber) AS PartNumber,
    COALESCE(h.EOLName, sf.EOLName) AS EOLName,
    CAST(((se.ScanAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time') AS date) AS ActivityDateLocal,
    CASE
        WHEN DATEPART(HOUR, ((se.ScanAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time')) BETWEEN 0 AND 7 THEN 'SHIFT_1'
        WHEN DATEPART(HOUR, ((se.ScanAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time')) BETWEEN 8 AND 15 THEN 'SHIFT_2'
        ELSE 'SHIFT_3'
    END AS ShiftLabel,
    COUNT(DISTINCT se.DollyNo) AS DollyCount,
    COUNT(*) AS VinCount,
    AVG(CASE WHEN h.LoadingCompletedAtUtc IS NOT NULL
             THEN DATEDIFF(SECOND, se.ScanAtUtc, h.LoadingCompletedAtUtc) END) AS AvgSec_ScanToLoadingCompleted,
    AVG(CASE WHEN sf.ASNSentAtUtc IS NOT NULL
             THEN DATEDIFF(SECOND, se.ScanAtUtc, sf.ASNSentAtUtc) END) AS AvgSec_ScanToASN,
    AVG(CASE WHEN sf.IrsaliyeSentAtUtc IS NOT NULL
             THEN DATEDIFF(SECOND, se.ScanAtUtc, sf.IrsaliyeSentAtUtc) END) AS AvgSec_ScanToIrsaliye
FROM scan_events se
LEFT JOIN hold_agg h ON se.DollyNo = h.DollyNo AND se.VinNo = h.VinNo
LEFT JOIN sefer_agg sf ON se.DollyNo = sf.DollyNo AND se.VinNo = sf.VinNo
WHERE se.ForkliftOperator IS NOT NULL
GROUP BY
    se.ForkliftOperator,
    COALESCE(h.PartNumber, sf.PartNumber),
    COALESCE(h.EOLName, sf.EOLName),
    CAST(((se.ScanAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time') AS date),
    CASE
        WHEN DATEPART(HOUR, ((se.ScanAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time')) BETWEEN 0 AND 7 THEN 'SHIFT_1'
        WHEN DATEPART(HOUR, ((se.ScanAtUtc AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time')) BETWEEN 8 AND 15 THEN 'SHIFT_2'
        ELSE 'SHIFT_3'
    END;

GO

-- ============================================================================
-- 6) WEB OPERATOR PERFORMANCE (daily + shift + part)
-- ============================================================================
IF OBJECT_ID('dbo.vw_Analytics_WebOperatorPerformanceDaily', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_WebOperatorPerformanceDaily;
GO

CREATE VIEW dbo.vw_Analytics_WebOperatorPerformanceDaily AS
SELECT
    s.VeriGirisUser AS WebOperator,
    s.PartNumber,
    CAST(((COALESCE(s.ASNDate, s.IrsaliyeDate, s.TerminalDate) AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time') AS date) AS ActivityDateLocal,
    CASE
        WHEN DATEPART(HOUR, ((COALESCE(s.ASNDate, s.IrsaliyeDate, s.TerminalDate) AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time')) BETWEEN 0 AND 7 THEN 'SHIFT_1'
        WHEN DATEPART(HOUR, ((COALESCE(s.ASNDate, s.IrsaliyeDate, s.TerminalDate) AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time')) BETWEEN 8 AND 15 THEN 'SHIFT_2'
        ELSE 'SHIFT_3'
    END AS ShiftLabel,
    COUNT(DISTINCT s.DollyNo) AS DollyCount,
    COUNT(*) AS VinCount,
    COUNT(CASE WHEN s.ASNDate IS NOT NULL THEN 1 END) AS ASNCount,
    COUNT(CASE WHEN s.IrsaliyeDate IS NOT NULL THEN 1 END) AS IrsaliyeCount,
    AVG(CASE WHEN h.LoadingCompletedAt IS NOT NULL AND COALESCE(s.ASNDate, s.IrsaliyeDate) IS NOT NULL
             THEN DATEDIFF(SECOND, h.LoadingCompletedAt, COALESCE(s.ASNDate, s.IrsaliyeDate)) END) AS AvgSec_LoadingToShipment,
    AVG(CASE WHEN h.CreatedAt IS NOT NULL AND COALESCE(s.ASNDate, s.IrsaliyeDate) IS NOT NULL
             THEN DATEDIFF(SECOND, h.CreatedAt, COALESCE(s.ASNDate, s.IrsaliyeDate)) END) AS AvgSec_ScanToShipment
FROM dbo.SeferDollyEOL s
LEFT JOIN dbo.DollySubmissionHold h ON s.DollyNo = h.DollyNo AND s.VinNo = h.VinNo
WHERE s.VeriGirisUser IS NOT NULL
GROUP BY
    s.VeriGirisUser,
    s.PartNumber,
    CAST(((COALESCE(s.ASNDate, s.IrsaliyeDate, s.TerminalDate) AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time') AS date),
    CASE
        WHEN DATEPART(HOUR, ((COALESCE(s.ASNDate, s.IrsaliyeDate, s.TerminalDate) AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time')) BETWEEN 0 AND 7 THEN 'SHIFT_1'
        WHEN DATEPART(HOUR, ((COALESCE(s.ASNDate, s.IrsaliyeDate, s.TerminalDate) AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time')) BETWEEN 8 AND 15 THEN 'SHIFT_2'
        ELSE 'SHIFT_3'
    END;

GO

-- ============================================================================
-- 6B) SHIFT SUMMARY (daily, all roles)
-- ============================================================================
IF OBJECT_ID('dbo.vw_Analytics_ShiftSummaryDaily', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_ShiftSummaryDaily;
GO

CREATE VIEW dbo.vw_Analytics_ShiftSummaryDaily AS
SELECT
    CAST(st.ShiftTimeLocal AS date) AS ActivityDateLocal,
    CASE
        WHEN DATEPART(HOUR, st.ShiftTimeLocal) BETWEEN 0 AND 7 THEN 'SHIFT_1'
        WHEN DATEPART(HOUR, st.ShiftTimeLocal) BETWEEN 8 AND 15 THEN 'SHIFT_2'
        ELSE 'SHIFT_3'
    END AS ShiftLabel,
    COUNT(*) AS VinCount,
    COUNT(DISTINCT tl.DollyNo) AS DollyCount,
    COUNT(DISTINCT tl.EOLName) AS EOLCount,
    COUNT(DISTINCT tl.PartNumber) AS PartCount,
    AVG(tl.Min_Production_To_FirstScan) AS AvgMin_ProductionToScan,
    AVG(tl.Min_FirstScan_To_LoadingCompleted) AS AvgMin_ScanToLoadingCompleted,
    AVG(tl.Min_Scan_To_Shipment) AS AvgMin_ScanToShipment,
    AVG(tl.Min_Production_To_Shipment) AS AvgMin_ProductionToShipment,
    COUNT(CASE WHEN tl.Min_Production_To_Shipment <= 270 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) AS OnTimePercent
FROM dbo.vw_Analytics_DollyTimelineDetailed tl
CROSS APPLY (
    SELECT COALESCE(
        tl.FirstScanAtLocal,
        tl.LoadingCompletedAtLocal,
        tl.ASNSentAtLocal,
        tl.IrsaliyeSentAtLocal,
        tl.ProductionRecordedAtLocal,
        tl.ProductionCompletedAtLocal
    ) AS ShiftTimeLocal
) st
WHERE st.ShiftTimeLocal IS NOT NULL
GROUP BY
    CAST(st.ShiftTimeLocal AS date),
    CASE
        WHEN DATEPART(HOUR, st.ShiftTimeLocal) BETWEEN 0 AND 7 THEN 'SHIFT_1'
        WHEN DATEPART(HOUR, st.ShiftTimeLocal) BETWEEN 8 AND 15 THEN 'SHIFT_2'
        ELSE 'SHIFT_3'
    END;

GO

-- ============================================================================
-- 7) GROUP + EOL PERFORMANCE (daily)
-- ============================================================================
IF OBJECT_ID('dbo.vw_Analytics_GroupEOLPerformanceDaily', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_GroupEOLPerformanceDaily;
GO

CREATE VIEW dbo.vw_Analytics_GroupEOLPerformanceDaily AS
SELECT
    tl.EOLName,
    tl.GroupName,
    tl.ShippingTag,
    CAST(tl.ProductionCompletedAtLocal AS date) AS ProductionDateLocal,
    COUNT(*) AS VinCount,
    COUNT(DISTINCT tl.DollyNo) AS DollyCount,
    AVG(tl.Min_Production_To_FirstScan) AS AvgMin_ProductionToScan,
    AVG(tl.Min_FirstScan_To_LoadingCompleted) AS AvgMin_ScanToLoadingCompleted,
    AVG(tl.Min_Scan_To_Shipment) AS AvgMin_ScanToShipment,
    AVG(tl.Min_Production_To_Shipment) AS AvgMin_ProductionToShipment
FROM dbo.vw_Analytics_DollyTimelineDetailed tl
GROUP BY tl.EOLName, tl.GroupName, tl.ShippingTag, CAST(tl.ProductionCompletedAtLocal AS date);

GO

-- ============================================================================
-- 8) TASK PERFORMANCE (per PartNumber)
-- ============================================================================
IF OBJECT_ID('dbo.vw_Analytics_TaskPerformance', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Analytics_TaskPerformance;
GO

CREATE VIEW dbo.vw_Analytics_TaskPerformance AS
SELECT
    t.PartNumber,
    t.Status AS TaskStatus,
    t.AssignedTo AS TaskAssignedToUserId,
    t.GroupTag,
    t.TotalItems,
    t.ProcessedItems,
    t.CreatedAt AS TaskCreatedAtUtc,
    t.CompletedAt AS TaskCompletedAtUtc,
    (t.CreatedAt AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS TaskCreatedAtLocal,
    (t.CompletedAt AT TIME ZONE 'UTC') AT TIME ZONE 'Turkey Standard Time' AS TaskCompletedAtLocal,
    DATEDIFF(MINUTE, t.CreatedAt, t.CompletedAt) AS Min_TaskDuration,
    COUNT(DISTINCT h.DollyNo) AS DollyCount,
    COUNT(*) AS VinCount
FROM dbo.WebOperatorTask t
LEFT JOIN dbo.DollySubmissionHold h ON h.PartNumber = t.PartNumber
GROUP BY
    t.PartNumber,
    t.Status,
    t.AssignedTo,
    t.GroupTag,
    t.TotalItems,
    t.ProcessedItems,
    t.CreatedAt,
    t.CompletedAt;

GO

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
