/*
  View & helper procedure that centralize all dolly relations shown on the ERD.
  The join between DollyEOLInfo.EOLID and DollyGroupEOL/PWorkStation assumes EOLID
  stores the related workstation id.  If it holds a different key (e.g. workstation no),
  adjust the ON clause accordingly.
*/

IF OBJECT_ID('dbo.vw_DollyControlTower', 'V') IS NOT NULL
    DROP VIEW dbo.vw_DollyControlTower;
GO

CREATE VIEW dbo.vw_DollyControlTower
AS
WITH LatestLifecycle AS (
    SELECT dl.*,
           ROW_NUMBER() OVER (PARTITION BY dl.DollyNo ORDER BY dl.CreatedAt DESC) AS rn
    FROM dbo.DollyLifecycle AS dl
),
LatestHold AS (
    SELECT dsh.*,
           ROW_NUMBER() OVER (PARTITION BY dsh.DollyNo, dsh.VinNo ORDER BY dsh.CreatedAt DESC) AS rn
    FROM dbo.DollySubmissionHold AS dsh
),
LatestAudit AS (
    SELECT al.*,
           ROW_NUMBER() OVER (PARTITION BY al.ResourceId ORDER BY al.CreatedAt DESC) AS rn
    FROM dbo.AuditLog AS al
    WHERE al.Resource = 'dolly'
)
SELECT
    de.DollyNo,
    de.VinNo,
    COALESCE(sde.PartNumber, lh.PartNumber, de.CustomerReferans) AS PartNumber,
    de.CustomerReferans,
    de.Adet,
    de.EOLName,
    de.EOLID,
    de.EOLDATE,
    de.EOLDollyBarcode,
    COALESCE(pw.PWorkStationName, de.EOLName) AS PWorkStationName,
    pw.PWorkStationNo,
    pw.GroupCode,
    pw.SpecCode1,
    pw.SpecCode2,
    dg.Id AS GroupId,
    dg.GroupName,
    dg.Description AS GroupDescription,
    dge.ShippingTag,
    ll.Status AS LifecycleStatus,
    ll.Source AS LifecycleSource,
    ll.Metadata AS LifecycleMetadata,
    ll.CreatedAt AS LifecycleCreatedAt,
    lh.Status AS HoldStatus,
    lh.Payload AS HoldPayload,
    lh.CreatedAt AS HoldCreatedAt,
    lh.SubmittedAt AS HoldSubmittedAt,
    lh.PartNumber AS HoldPartNumber,
    tu.DisplayName AS HoldTerminalUser,
    sde.SeferNumarasi,
    sde.PlakaNo,
    sde.CustomerReferans AS SeferCustomerRef,
    sde.Adet AS SeferCount,
    sde.TerminalDate,
    sde.ASNDate,
    sde.IrsaliyeDate,
    la.ActorType AS AuditActorType,
    la.ActorId AS AuditActorId,
    la.ActorName AS AuditActorName,
    la.Action AS AuditAction,
    la.Payload AS AuditPayload,
    la.CreatedAt AS AuditCreatedAt,
    wot.Id AS WebTaskId,
    wot.PartNumber,
    wot.Status AS WebTaskStatus,
    wot.AssignedTo,
    wot.GroupTag,
    wot.TotalItems,
    wot.ProcessedItems,
    CASE
        WHEN ISNULL(wot.TotalItems, 0) = 0 THEN NULL
        ELSE CAST(wot.ProcessedItems AS decimal(10,2)) / NULLIF(wot.TotalItems, 0) * 100
    END AS WebTaskProgressPct,
    wot.CreatedAt AS WebTaskCreatedAt,
    wot.UpdatedAt AS WebTaskUpdatedAt,
    GETUTCDATE() AS SnapshotTakenAt
FROM dbo.DollyEOLInfo AS de
LEFT JOIN LatestLifecycle AS ll
       ON ll.DollyNo = de.DollyNo AND ll.rn = 1
LEFT JOIN LatestHold AS lh
       ON lh.DollyNo = de.DollyNo AND lh.VinNo = de.VinNo AND lh.rn = 1
LEFT JOIN dbo.UserAccount AS tu
       ON tu.Username = lh.TerminalUser
LEFT JOIN dbo.SeferDollyEOL AS sde
       ON sde.DollyNo = de.DollyNo AND sde.VinNo = de.VinNo
LEFT JOIN LatestAudit AS la
       ON la.ResourceId = de.DollyNo AND la.rn = 1
LEFT JOIN dbo.DollyGroupEOL AS dge
       ON dge.PWorkStationId = de.EOLID
LEFT JOIN dbo.DollyGroup AS dg
       ON dg.Id = dge.GroupId
LEFT JOIN dbo.PWorkStation AS pw
       ON pw.Id = dge.PWorkStationId
LEFT JOIN dbo.WebOperatorTask AS wot
       ON wot.PartNumber = de.CustomerReferans
      AND wot.Status NOT IN ('completed', 'cancelled');
GO


IF OBJECT_ID('dbo.sp_GetDollyQueueSnapshot', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_GetDollyQueueSnapshot;
GO

CREATE PROCEDURE dbo.sp_GetDollyQueueSnapshot
    @GroupId        INT           = NULL,
    @OnlyPendingHolds BIT         = 0,
    @SearchTerm     NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        v.DollyNo,
        v.VinNo,
        v.PartNumber,
        v.CustomerReferans,
        v.Adet,
        v.EOLName,
        v.PWorkStationName,
        v.GroupName,
        v.ShippingTag,
        v.LifecycleStatus,
        v.HoldStatus,
        v.HoldTerminalUser,
        v.WebTaskStatus,
        v.WebTaskProgressPct,
        v.SeferNumarasi,
        v.ASNDate,
        v.AuditAction,
        v.SnapshotTakenAt
    FROM dbo.vw_DollyControlTower AS v
    WHERE (@GroupId IS NULL OR v.GroupId = @GroupId)
      AND (@OnlyPendingHolds = 0 OR v.HoldStatus IS NOT NULL)
      AND (
            @SearchTerm IS NULL
            OR v.DollyNo LIKE '%' + @SearchTerm + '%'
            OR v.VinNo LIKE '%' + @SearchTerm + '%'
            OR v.CustomerReferans LIKE '%' + @SearchTerm + '%'
            OR v.PartNumber LIKE '%' + @SearchTerm + '%'
            OR v.PWorkStationName LIKE '%' + @SearchTerm + '%'
          )
    ORDER BY
        v.ASNDate DESC,
        v.EOLDATE DESC,
        v.DollyNo,
        v.VinNo;
END;
GO
