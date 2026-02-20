-- =============================================
-- Dolly Queue Removed Archive System
-- Created: 14 Ocak 2026
-- Purpose: Sıradan manuel olarak kaldırılan dolly'leri arşivlemek
-- =============================================

-- Check if table exists
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DollyQueueRemoved')
BEGIN
    CREATE TABLE [dbo].[DollyQueueRemoved] (
        -- Primary Key
        [Id] INT IDENTITY(1,1) PRIMARY KEY,
        
        -- DollyEOLInfo'dan kopyalanan alanlar
        [DollyNo] INT NOT NULL,
        [VinNo] NVARCHAR(50) NOT NULL,
        [CustomerReferans] NVARCHAR(50) NULL,
        [Adet] INT NULL,
        [EOLName] NVARCHAR(50) NULL,
        [EOLID] NVARCHAR(20) NULL,
        [EOLDATE] DATE NULL,
        [EOLDollyBarcode] NVARCHAR(100) NULL,
        [DollyOrderNo] VARCHAR(20) NULL,
        [RECEIPTID] INT NULL,
        [OriginalInsertedAt] DATETIME2 NULL,
        
        -- Arşiv metadata
        [RemovedAt] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [RemovedBy] NVARCHAR(100) NULL,
        [RemovalReason] NVARCHAR(500) NULL
    );
    
    -- Unique constraint
    CREATE UNIQUE NONCLUSTERED INDEX [IX_DollyQueueRemoved_DollyNo]
    ON [dbo].[DollyQueueRemoved] ([DollyNo], [VinNo], [RemovedAt]);
    
    PRINT 'DollyQueueRemoved tablosu oluşturuldu.';
END
ELSE
BEGIN
    PRINT 'DollyQueueRemoved tablosu zaten mevcut.';
END
GO

-- Index for removed records
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_DollyQueueRemoved_RemovedAt')
BEGIN
    CREATE NONCLUSTERED INDEX [IX_DollyQueueRemoved_RemovedAt]
    ON [dbo].[DollyQueueRemoved] ([RemovedAt] DESC);
    
    PRINT 'RemovedAt index oluşturuldu.';
END
GO

PRINT '✅ Migration 016 başarıyla tamamlandı.';
GO
