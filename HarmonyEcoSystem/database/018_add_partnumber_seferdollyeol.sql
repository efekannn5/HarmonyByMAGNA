-- Migration: Add PartNumber column to SeferDollyEOL
-- Purpose: Store PartNumber alongside shipment history for reporting/filtering
-- Date: 2026-01

USE dollydb_test;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.SeferDollyEOL')
      AND name = 'PartNumber'
)
BEGIN
    ALTER TABLE dbo.SeferDollyEOL
    ADD PartNumber NVARCHAR(50) NULL;

    PRINT '✅ Added PartNumber column to SeferDollyEOL';
END
ELSE
BEGIN
    PRINT 'ℹ️ PartNumber already exists on SeferDollyEOL';
END
GO
