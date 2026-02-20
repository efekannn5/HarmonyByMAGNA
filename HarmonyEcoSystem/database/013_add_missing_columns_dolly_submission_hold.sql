/*
  Migration: Ensure all required columns exist in DollySubmissionHold
  
  Purpose: Add missing columns for complete workflow tracking
*/

-- Add PartNumber if not exists
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'PartNumber'
)
BEGIN
    ALTER TABLE [dbo].[DollySubmissionHold]
    ADD [PartNumber] NVARCHAR(50) NULL;
    
    PRINT '✅ Added PartNumber column to DollySubmissionHold';
END
ELSE
BEGIN
    PRINT 'ℹ️ PartNumber column already exists in DollySubmissionHold';
END;
GO

-- Add CustomerReferans if not exists
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'CustomerReferans'
)
BEGIN
    ALTER TABLE [dbo].[DollySubmissionHold]
    ADD [CustomerReferans] NVARCHAR(50) NULL;
    
    PRINT '✅ Added CustomerReferans column to DollySubmissionHold';
END
ELSE
BEGIN
    PRINT 'ℹ️ CustomerReferans column already exists in DollySubmissionHold';
END;
GO

-- Add EOLName if not exists
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'EOLName'
)
BEGIN
    ALTER TABLE [dbo].[DollySubmissionHold]
    ADD [EOLName] NVARCHAR(50) NULL;
    
    PRINT '✅ Added EOLName column to DollySubmissionHold';
END
ELSE
BEGIN
    PRINT 'ℹ️ EOLName column already exists in DollySubmissionHold';
END;
GO

-- Add EOLID if not exists
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'EOLID'
)
BEGIN
    ALTER TABLE [dbo].[DollySubmissionHold]
    ADD [EOLID] NVARCHAR(20) NULL;
    
    PRINT '✅ Added EOLID column to DollySubmissionHold';
END
ELSE
BEGIN
    PRINT 'ℹ️ EOLID column already exists in DollySubmissionHold';
END;
GO

-- Add DollyOrderNo if not exists
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'DollyOrderNo'
)
BEGIN
    ALTER TABLE [dbo].[DollySubmissionHold]
    ADD [DollyOrderNo] NVARCHAR(20) NULL;
    
    PRINT '✅ Added DollyOrderNo column to DollySubmissionHold';
END
ELSE
BEGIN
    PRINT 'ℹ️ DollyOrderNo column already exists in DollySubmissionHold';
END;
GO

-- Add Adet if not exists
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
    AND name = 'Adet'
)
BEGIN
    ALTER TABLE [dbo].[DollySubmissionHold]
    ADD [Adet] INT NULL DEFAULT 1;
    
    PRINT '✅ Added Adet column to DollySubmissionHold';
END
ELSE
BEGIN
    PRINT 'ℹ️ Adet column already exists in DollySubmissionHold';
END;
GO

-- Create composite index for performance
IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'IX_DollySubmissionHold_DollyNo_VinNo' 
    AND object_id = OBJECT_ID('dbo.DollySubmissionHold')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_DollySubmissionHold_DollyNo_VinNo
        ON [dbo].[DollySubmissionHold] ([DollyNo], [VinNo]) 
        INCLUDE ([Status], [CreatedAt]);
    
    PRINT '✅ Created composite index IX_DollySubmissionHold_DollyNo_VinNo';
END
ELSE
BEGIN
    PRINT 'ℹ️ Index IX_DollySubmissionHold_DollyNo_VinNo already exists';
END;
GO

PRINT '✅ Migration 013 completed successfully';
