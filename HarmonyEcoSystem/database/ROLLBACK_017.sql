-- ============================================================
-- ROLLBACK Script for Migration 017
-- Purpose: Remove ASNSent and IrsaliyeSent columns if needed
-- WARNING: This will delete the columns and their data!
-- ============================================================

USE dollydb_test;
GO

PRINT '========================================';
PRINT 'ROLLBACK Migration 017';
PRINT 'WARNING: This will remove the columns!';
PRINT '========================================';
PRINT '';

-- Check if columns exist before dropping
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

-- Drop ASNSent if exists
IF @ASNSentExists > 0
BEGIN
    PRINT 'Removing ASNSent column...';
    ALTER TABLE dbo.DollySubmissionHold DROP COLUMN ASNSent;
    PRINT '  ✓ ASNSent column removed';
END
ELSE
BEGIN
    PRINT '  ℹ ASNSent column does not exist, skipping';
END

-- Drop IrsaliyeSent if exists
IF @IrsaliyeSentExists > 0
BEGIN
    PRINT 'Removing IrsaliyeSent column...';
    ALTER TABLE dbo.DollySubmissionHold DROP COLUMN IrsaliyeSent;
    PRINT '  ✓ IrsaliyeSent column removed';
END
ELSE
BEGIN
    PRINT '  ℹ IrsaliyeSent column does not exist, skipping';
END

PRINT '';
PRINT '✓ Rollback completed';
GO
