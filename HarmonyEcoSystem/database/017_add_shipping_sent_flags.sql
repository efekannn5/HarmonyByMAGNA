-- Migration: Add shipping sent flags to DollySubmissionHold
-- Purpose: Track ASN and Irsaliye submissions separately for 'both' tagged items
-- Date: 2024

USE dollydb_test;
GO

-- Add ASNSent and IrsaliyeSent flags
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'ASNSent'
)
BEGIN
    ALTER TABLE dbo.DollySubmissionHold 
    ADD ASNSent BIT NOT NULL DEFAULT 0;
    
    PRINT '✅ Added ASNSent column to DollySubmissionHold';
END
ELSE
BEGIN
    PRINT 'ℹ️  ASNSent column already exists';
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'IrsaliyeSent'
)
BEGIN
    ALTER TABLE dbo.DollySubmissionHold 
    ADD IrsaliyeSent BIT NOT NULL DEFAULT 0;
    
    PRINT '✅ Added IrsaliyeSent column to DollySubmissionHold';
END
ELSE
BEGIN
    PRINT 'ℹ️  IrsaliyeSent column already exists';
END
GO

PRINT '✅ Migration 017 completed successfully';
GO
