IF OBJECT_ID('[dbo].[AuditLog]', 'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[AuditLog] (
        [Id]          INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [ActorType]   NVARCHAR(30)      NOT NULL,
        [ActorId]     INT               NULL,
        [ActorName]   NVARCHAR(120)     NULL,
        [Action]      NVARCHAR(80)      NOT NULL,
        [Resource]    NVARCHAR(80)      NULL,
        [ResourceId]  NVARCHAR(80)      NULL,
        [Payload]     NVARCHAR(MAX)     NULL,
        [CreatedAt]   DATETIME2(0)      NOT NULL CONSTRAINT DF_AuditLog_CreatedAt DEFAULT (SYSUTCDATETIME())
    );
END;
