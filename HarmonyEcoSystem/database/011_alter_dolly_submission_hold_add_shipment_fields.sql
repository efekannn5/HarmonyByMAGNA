/*
  Migration: Add shipment-related fields to DollySubmissionHold
  
  Purpose: Support the new workflow:
  1. Forklift scans dollys in order (ScanOrder tracks sequence)
  2. Forklift submits loading completion (LoadingCompletedAt)
  3. Web operator adds shipment details (SeferNumarasi, PlakaNo)
  4. Web operator sends ASN/Irsaliye
*/

-- Add ScanOrder column for tracking sequence of scans
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'ScanOrder'
)
BEGIN
    ALTER TABLE [dbo].[DollySubmissionHold]
    ADD [ScanOrder] INT NULL;
    
    PRINT 'Added ScanOrder column to DollySubmissionHold';
END
ELSE
BEGIN
    PRINT 'ScanOrder column already exists in DollySubmissionHold';
END;
GO

-- Add SeferNumarasi column (shipment number)
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'SeferNumarasi'
)
BEGIN
    ALTER TABLE [dbo].[DollySubmissionHold]
    ADD [SeferNumarasi] NVARCHAR(20) NULL;
    
    PRINT 'Added SeferNumarasi column to DollySubmissionHold';
END
ELSE
BEGIN
    PRINT 'SeferNumarasi column already exists in DollySubmissionHold';
END;
GO

-- Add PlakaNo column (truck plate number)
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'PlakaNo'
)
BEGIN
    ALTER TABLE [dbo].[DollySubmissionHold]
    ADD [PlakaNo] NVARCHAR(20) NULL;
    
    PRINT 'Added PlakaNo column to DollySubmissionHold';
END
ELSE
BEGIN
    PRINT 'PlakaNo column already exists in DollySubmissionHold';
END;
GO

-- Add LoadingCompletedAt column (when forklift completed loading)
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'LoadingCompletedAt'
)
BEGIN
    ALTER TABLE [dbo].[DollySubmissionHold]
    ADD [LoadingCompletedAt] DATETIME2(0) NULL;
    
    PRINT 'Added LoadingCompletedAt column to DollySubmissionHold';
END
ELSE
BEGIN
    PRINT 'LoadingCompletedAt column already exists in DollySubmissionHold';
END;
GO

-- Add LoadingSessionId column (group multiple scans into one loading session)
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'LoadingSessionId'
)
BEGIN
    ALTER TABLE [dbo].[DollySubmissionHold]
    ADD [LoadingSessionId] NVARCHAR(50) NULL;
    
    PRINT 'Added LoadingSessionId column to DollySubmissionHold';
END
ELSE
BEGIN
    PRINT 'LoadingSessionId column already exists in DollySubmissionHold';
END;
GO

-- Create index for better query performance
IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'IX_DollySubmissionHold_LoadingSession'
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_DollySubmissionHold_LoadingSession
        ON [dbo].[DollySubmissionHold] ([LoadingSessionId], [ScanOrder])
        INCLUDE ([DollyNo], [VinNo], [Status], [CreatedAt]);
    
    PRINT 'Created index IX_DollySubmissionHold_LoadingSession';
END
ELSE
BEGIN
    PRINT 'Index IX_DollySubmissionHold_LoadingSession already exists';
END;
GO

-- Create index for shipment queries
IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'IX_DollySubmissionHold_Shipment'
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_DollySubmissionHold_Shipment
        ON [dbo].[DollySubmissionHold] ([SeferNumarasi])
        INCLUDE ([PlakaNo], [Status], [LoadingCompletedAt]);
    
    PRINT 'Created index IX_DollySubmissionHold_Shipment';
END
ELSE
BEGIN
    PRINT 'Index IX_DollySubmissionHold_Shipment already exists';
END;
GO

PRINT 'Migration 011 completed successfully';
