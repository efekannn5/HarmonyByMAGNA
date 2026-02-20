-- ============================================================================
-- Migration #020: Extend String Columns (NVARCHAR(50) → NVARCHAR(100))
-- ============================================================================
-- Purpose: Fix truncation error for long PartNumbers and LoadingSessionId
-- Date: 2026-01-21
-- Author: System Migration
-- Issue: PartNumber and LoadingSessionId can exceed 50 characters causing SQL error
-- ============================================================================

USE ControlTower;
GO

PRINT '========================================';
PRINT 'Migration #020: Extend String Columns';
PRINT '========================================';
GO

-- 1. Extend PartNumber in DollySubmissionHold
IF EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('DollySubmissionHold') 
    AND name = 'PartNumber'
)
BEGIN
    PRINT '✓ Extending DollySubmissionHold.PartNumber to NVARCHAR(100)...';
    ALTER TABLE DollySubmissionHold
    ALTER COLUMN PartNumber NVARCHAR(100) NULL;
    PRINT '  ✓ DollySubmissionHold.PartNumber updated';
END
ELSE
BEGIN
    PRINT '⚠ DollySubmissionHold.PartNumber column not found, skipping...';
END
GO

-- 2. Extend PartNumber in SeferDollyEOL
IF EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('SeferDollyEOL') 
    AND name = 'PartNumber'
)
BEGIN
    PRINT '✓ Extending SeferDollyEOL.PartNumber to NVARCHAR(100)...';
    ALTER TABLE SeferDollyEOL
    ALTER COLUMN PartNumber NVARCHAR(100) NULL;
    PRINT '  ✓ SeferDollyEOL.PartNumber updated';
END
ELSE
BEGIN
    PRINT '⚠ SeferDollyEOL.PartNumber column not found, skipping...';
END
GO

-- 3. Extend PartNumber in DollyEOLInfo
IF EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('DollyEOLInfo') 
    AND name = 'PartNumber'
)
BEGIN
    PRINT '✓ Extending DollyEOLInfo.PartNumber to NVARCHAR(100)...';
    ALTER TABLE DollyEOLInfo
    ALTER COLUMN PartNumber NVARCHAR(100) NULL;
    PRINT '  ✓ DollyEOLInfo.PartNumber updated';
END
ELSE
BEGIN
    PRINT '⚠ DollyEOLInfo.PartNumber column not found, skipping...';
END
GO

-- 4. Extend LoadingSessionId in DollySubmissionHold
IF EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('DollySubmissionHold') 
    AND name = 'LoadingSessionId'
)
BEGIN
    PRINT '✓ Extending DollySubmissionHold.LoadingSessionId to NVARCHAR(100)...';
    ALTER TABLE DollySubmissionHold
    ALTER COLUMN LoadingSessionId NVARCHAR(100) NULL;
    PRINT '  ✓ DollySubmissionHold.LoadingSessionId updated';
END
ELSE
BEGIN
    PRINT '⚠ DollySubmissionHold.LoadingSessionId column not found, skipping...';
END
GO

-- 5. Verification
PRINT '';
PRINT '========================================';
PRINT 'Verification:';
PRINT '========================================';

SELECT 
    TABLE_NAME, 
    COLUMN_NAME, 
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH AS MaxLength
FROM INFORMATION_SCHEMA.COLUMNS
WHERE (COLUMN_NAME = 'PartNumber' OR COLUMN_NAME = 'LoadingSessionId')
AND TABLE_NAME IN ('DollySubmissionHold', 'SeferDollyEOL', 'DollyEOLInfo')
ORDER BY TABLE_NAME, COLUMN_NAME;

PRINT '';
PRINT '========================================';
PRINT '✓ Migration #020 completed successfully!';
PRINT '========================================';
GO
