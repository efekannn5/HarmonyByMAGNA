-- ============================================================
-- Migration 017: Add ASNSent and IrsaliyeSent flags
-- Purpose: Track ASN and Irsaliye submissions separately for 'both' tagged items
-- Date: 17 Ocak 2026
-- SAFE: Checks before adding, won't break existing system
-- ============================================================

USE dollydb_test;
GO

PRINT '========================================';
PRINT 'Migration 017: ASNSent & IrsaliyeSent';
PRINT '========================================';
PRINT '';

-- ============================================================
-- STEP 1: Check existing columns
-- ============================================================
PRINT 'STEP 1: Checking existing columns...';

DECLARE @ASNSentExists INT = 0;
DECLARE @IrsaliyeSentExists INT = 0;

SELECT @ASNSentExists = COUNT(*) 
FROM sys.columns 
WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
AND name = 'ASNSent';

SELECT @IrsaliyeSentExists = COUNT(*) 
FROM sys.columns 
WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
AND name = 'IrsaliyeSent';

IF @ASNSentExists > 0
    PRINT '  ✓ ASNSent column already exists';
ELSE
    PRINT '  ✗ ASNSent column does not exist';

IF @IrsaliyeSentExists > 0
    PRINT '  ✓ IrsaliyeSent column already exists';
ELSE
    PRINT '  ✗ IrsaliyeSent column does not exist';

PRINT '';

-- ============================================================
-- STEP 2: Add ASNSent column (safe)
-- ============================================================
IF @ASNSentExists = 0
BEGIN
    PRINT 'STEP 2: Adding ASNSent column...';
    
    BEGIN TRY
        ALTER TABLE dbo.DollySubmissionHold 
        ADD ASNSent BIT NOT NULL DEFAULT 0;
        
        PRINT '  ✓ ASNSent column added successfully';
        PRINT '    - Type: BIT';
        PRINT '    - Nullable: NO';
        PRINT '    - Default: 0 (False)';
    END TRY
    BEGIN CATCH
        PRINT '  ✗ ERROR adding ASNSent: ' + ERROR_MESSAGE();
        THROW;
    END CATCH
END
ELSE
BEGIN
    PRINT 'STEP 2: ASNSent column already exists, skipping...';
END

PRINT '';

-- ============================================================
-- STEP 3: Add IrsaliyeSent column (safe)
-- ============================================================
IF @IrsaliyeSentExists = 0
BEGIN
    PRINT 'STEP 3: Adding IrsaliyeSent column...';
    
    BEGIN TRY
        ALTER TABLE dbo.DollySubmissionHold 
        ADD IrsaliyeSent BIT NOT NULL DEFAULT 0;
        
        PRINT '  ✓ IrsaliyeSent column added successfully';
        PRINT '    - Type: BIT';
        PRINT '    - Nullable: NO';
        PRINT '    - Default: 0 (False)';
    END TRY
    BEGIN CATCH
        PRINT '  ✗ ERROR adding IrsaliyeSent: ' + ERROR_MESSAGE();
        THROW;
    END CATCH
END
ELSE
BEGIN
    PRINT 'STEP 3: IrsaliyeSent column already exists, skipping...';
END

PRINT '';

-- ============================================================
-- STEP 4: Verify migration
-- ============================================================
PRINT 'STEP 4: Verifying migration...';

SELECT 
    COLUMN_NAME as 'Column',
    DATA_TYPE as 'Type',
    IS_NULLABLE as 'Nullable',
    COLUMN_DEFAULT as 'Default'
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'DollySubmissionHold'
AND COLUMN_NAME IN ('ASNSent', 'IrsaliyeSent')
ORDER BY COLUMN_NAME;

PRINT '';
PRINT '========================================';
PRINT '✓ Migration 017 completed successfully!';
PRINT '========================================';
GO
