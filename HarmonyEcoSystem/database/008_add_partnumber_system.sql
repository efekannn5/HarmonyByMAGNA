-- Add PartNumber system for web operator workflow

-- Add PartNumber to DollySubmissionHold table
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('[dbo].[DollySubmissionHold]') AND name = 'PartNumber')
BEGIN
    ALTER TABLE [dbo].[DollySubmissionHold]
    ADD [PartNumber] NVARCHAR(50) NULL;
    
    PRINT 'Added PartNumber column to DollySubmissionHold table.';
END

-- Add PartNumber to SeferDollyEOL table 
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('[dbo].[SeferDollyEOL]') AND name = 'PartNumber')
BEGIN
    ALTER TABLE [dbo].[SeferDollyEOL]
    ADD [PartNumber] NVARCHAR(50) NULL;
    
    PRINT 'Added PartNumber column to SeferDollyEOL table.';
END

-- Create index for PartNumber lookups
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID('[dbo].[DollySubmissionHold]') AND name = 'IX_DollySubmissionHold_PartNumber')
BEGIN
    CREATE NONCLUSTERED INDEX IX_DollySubmissionHold_PartNumber
        ON [dbo].[DollySubmissionHold] ([PartNumber]) INCLUDE ([Status], [CreatedAt]);
    
    PRINT 'Created index on PartNumber for DollySubmissionHold table.';
END

-- Create WebOperatorTask table for tracking operator assignments
IF OBJECT_ID('[dbo].[WebOperatorTask]', 'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[WebOperatorTask] (
        [Id]            INT IDENTITY(1,1)     NOT NULL PRIMARY KEY,
        [PartNumber]    NVARCHAR(50)          NOT NULL UNIQUE,
        [Status]        NVARCHAR(20)          NOT NULL CONSTRAINT DF_WebOperatorTask_Status DEFAULT ('pending'),
        [AssignedTo]    INT                   NULL,  -- UserAccount.Id
        [GroupTag]      NVARCHAR(20)          NOT NULL CONSTRAINT DF_WebOperatorTask_GroupTag DEFAULT ('both'), -- asn, irsaliye, both
        [TotalItems]    INT                   NOT NULL DEFAULT (0),
        [ProcessedItems] INT                  NOT NULL DEFAULT (0),
        [Metadata]      NVARCHAR(MAX)         NULL,
        [CreatedAt]     DATETIME2(0)          NOT NULL CONSTRAINT DF_WebOperatorTask_CreatedAt DEFAULT (SYSUTCDATETIME()),
        [UpdatedAt]     DATETIME2(0)          NOT NULL CONSTRAINT DF_WebOperatorTask_UpdatedAt DEFAULT (SYSUTCDATETIME()),
        [CompletedAt]   DATETIME2(0)          NULL,
        
        CONSTRAINT FK_WebOperatorTask_AssignedTo FOREIGN KEY ([AssignedTo]) REFERENCES [UserAccount]([Id])
    );
    
    CREATE NONCLUSTERED INDEX IX_WebOperatorTask_Status
        ON [dbo].[WebOperatorTask] ([Status]) INCLUDE ([PartNumber], [CreatedAt]);
        
    CREATE NONCLUSTERED INDEX IX_WebOperatorTask_AssignedTo
        ON [dbo].[WebOperatorTask] ([AssignedTo]) INCLUDE ([Status], [PartNumber]);
    
    PRINT 'Created WebOperatorTask table with indexes.';
END

-- Create function to generate unique PartNumber
IF OBJECT_ID('[dbo].[fn_GeneratePartNumber]', 'FN') IS NULL
BEGIN
    EXEC('
    CREATE FUNCTION [dbo].[fn_GeneratePartNumber]()
    RETURNS NVARCHAR(50)
    AS
    BEGIN
        DECLARE @PartNumber NVARCHAR(50)
        DECLARE @Date NVARCHAR(8) = FORMAT(GETDATE(), ''yyyyMMdd'')
        DECLARE @Counter INT
        
        -- Get next counter for today
        SELECT @Counter = ISNULL(MAX(CAST(RIGHT(PartNumber, 4) AS INT)), 0) + 1
        FROM DollySubmissionHold
        WHERE PartNumber LIKE ''PT'' + @Date + ''%''
        
        SET @PartNumber = ''PT'' + @Date + RIGHT(''0000'' + CAST(@Counter AS NVARCHAR(4)), 4)
        
        RETURN @PartNumber
    END')
    
    PRINT 'Created fn_GeneratePartNumber function.';
END