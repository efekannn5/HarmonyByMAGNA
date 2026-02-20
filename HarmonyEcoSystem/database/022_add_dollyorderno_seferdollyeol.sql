-- Migration 022: Add DollyOrderNo to SeferDollyEOL (idempotent)
-- Expected by ORM models and history screens.

IF NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.SeferDollyEOL')
      AND name = 'DollyOrderNo'
)
BEGIN
    PRINT '➕ Adding DollyOrderNo (NVARCHAR(50) NULL) to SeferDollyEOL...';
    ALTER TABLE dbo.SeferDollyEOL
        ADD DollyOrderNo NVARCHAR(50) NULL;
    PRINT '✅ DollyOrderNo column added.';
END
ELSE
BEGIN
    PRINT 'ℹ️  DollyOrderNo already exists on SeferDollyEOL. No action taken.';
END
