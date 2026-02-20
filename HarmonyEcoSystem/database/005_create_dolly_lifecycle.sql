IF OBJECT_ID('[dbo].[DollyLifecycle]', 'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[DollyLifecycle] (
        [Id]        INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [DollyNo]   NVARCHAR(20)      NOT NULL,
        [VinNo]     NVARCHAR(50)      NOT NULL,
        [Status]    NVARCHAR(40)      NOT NULL,
        [Source]    NVARCHAR(30)      NULL,
        [Metadata]  NVARCHAR(MAX)     NULL,
        [CreatedAt] DATETIME2(0)      NOT NULL CONSTRAINT DF_DollyLifecycle_CreatedAt DEFAULT (SYSUTCDATETIME())
    );

    CREATE INDEX IX_DollyLifecycle_DollyNo
        ON [dbo].[DollyLifecycle] ([DollyNo], [CreatedAt] DESC);
END;
