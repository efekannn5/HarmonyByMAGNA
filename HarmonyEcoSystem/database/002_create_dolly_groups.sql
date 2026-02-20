IF OBJECT_ID('[dbo].[DollyGroup]', 'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[DollyGroup] (
        [Id]            INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [GroupName]     NVARCHAR(100)    NOT NULL,
        [Description]   NVARCHAR(255)    NULL,
        [IsActive]      BIT              NOT NULL CONSTRAINT DF_DollyGroup_IsActive DEFAULT (1),
        [CreatedAt]     DATETIME2(0)     NOT NULL CONSTRAINT DF_DollyGroup_CreatedAt DEFAULT (SYSUTCDATETIME()),
        [UpdatedAt]     DATETIME2(0)     NOT NULL CONSTRAINT DF_DollyGroup_UpdatedAt DEFAULT (SYSUTCDATETIME())
    );
END;

IF OBJECT_ID('[dbo].[DollyGroupEOL]', 'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[DollyGroupEOL] (
        [Id]             INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [GroupId]        INT              NOT NULL,
        [PWorkStationId] INT              NOT NULL,
        [CreatedAt]      DATETIME2(0)     NOT NULL CONSTRAINT DF_DollyGroupEOL_CreatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_DollyGroupEOL_Group FOREIGN KEY (GroupId) REFERENCES [dbo].[DollyGroup](Id),
        CONSTRAINT FK_DollyGroupEOL_PWorkStation FOREIGN KEY (PWorkStationId) REFERENCES [dbo].[PWorkStation](Id)
    );
END;

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes WHERE name = 'UX_DollyGroupEOL_Group_Station'
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_DollyGroupEOL_Group_Station
        ON [dbo].[DollyGroupEOL] ([GroupId], [PWorkStationId]);
END;
