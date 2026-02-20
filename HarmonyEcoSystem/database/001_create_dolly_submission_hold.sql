IF OBJECT_ID('[dbo].[DollySubmissionHold]', 'U') IS NOT NULL
BEGIN
    PRINT 'Table DollySubmissionHold already exists.';
    RETURN;
END;

CREATE TABLE [dbo].[DollySubmissionHold] (
    [Id]            INT IDENTITY(1,1)     NOT NULL PRIMARY KEY,
    [DollyNo]       NVARCHAR(20)          NOT NULL,
    [VinNo]         NVARCHAR(50)          NOT NULL,
    [Status]        NVARCHAR(20)          NOT NULL CONSTRAINT DF_DollySubmissionHold_Status DEFAULT ('holding'),
    [TerminalUser]  NVARCHAR(100)         NULL,
    [Payload]       NVARCHAR(MAX)         NULL,
    [CreatedAt]     DATETIME2(0)          NOT NULL CONSTRAINT DF_DollySubmissionHold_CreatedAt DEFAULT (SYSUTCDATETIME()),
    [UpdatedAt]     DATETIME2(0)          NOT NULL CONSTRAINT DF_DollySubmissionHold_UpdatedAt DEFAULT (SYSUTCDATETIME()),
    [SubmittedAt]   DATETIME2(0)          NULL
);

CREATE NONCLUSTERED INDEX IX_DollySubmissionHold_Status
    ON [dbo].[DollySubmissionHold] ([Status]) INCLUDE ([DollyNo], [VinNo], [CreatedAt]);
