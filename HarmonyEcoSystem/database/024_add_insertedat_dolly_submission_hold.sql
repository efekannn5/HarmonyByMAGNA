/*
  Migration: Add InsertedAt column to DollySubmissionHold
  
  Purpose: Preserve original EOL timestamp from DollyEOLInfo for correct sorting
  
  Why: Dashboard sorting relies on InsertedAt (EOL timestamp) but it wasn't being
       copied during DollyEOLInfo → DollySubmissionHold transfer. This caused
       VIN ordering to break despite correct sorting logic.
       
  Fix: Add InsertedAt field and populate it from DollyEOLInfo.InsertedAt during transfer
*/

-- Add InsertedAt if not exists
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'InsertedAt'
)
BEGIN
    ALTER TABLE [dbo].[DollySubmissionHold]
    ADD [InsertedAt] DATETIME2 NULL;
    
    PRINT '✅ Added InsertedAt column to DollySubmissionHold';
    PRINT 'ℹ️  This field preserves original EOL timestamp for correct sorting';
END
ELSE
BEGIN
    PRINT 'ℹ️ InsertedAt column already exists in DollySubmissionHold';
END;
GO

PRINT '';
PRINT '========================================';
PRINT '✅ Migration 024 completed successfully';
PRINT '========================================';
