IF OBJECT_ID('[dbo].[UserRole]', 'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[UserRole] (
        [Id]          INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [Name]        NVARCHAR(40)      NOT NULL,
        [Description] NVARCHAR(255)     NULL,
        [CreatedAt]   DATETIME2(0)      NOT NULL CONSTRAINT DF_UserRole_CreatedAt DEFAULT (SYSUTCDATETIME())
    );
    INSERT INTO [dbo].[UserRole] ([Name], [Description])
    VALUES ('admin', 'Full control over web dashboard and terminal settings'),
           ('operator', 'View/acknowledge dolly queue on web'),
           ('terminal_admin', 'Configure forklift devices'),
           ('terminal_operator', 'Use forklift scanner features');
END;

IF OBJECT_ID('[dbo].[UserAccount]', 'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[UserAccount] (
        [Id]            INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [Username]      NVARCHAR(80)      NOT NULL UNIQUE,
        [DisplayName]   NVARCHAR(120)     NULL,
        [PasswordHash]  NVARCHAR(255)     NOT NULL,
        [RoleId]        INT               NOT NULL,
        [IsActive]      BIT               NOT NULL CONSTRAINT DF_UserAccount_IsActive DEFAULT (1),
        [LastLoginAt]   DATETIME2(0)      NULL,
        [CreatedAt]     DATETIME2(0)      NOT NULL CONSTRAINT DF_UserAccount_CreatedAt DEFAULT (SYSUTCDATETIME()),
        [UpdatedAt]     DATETIME2(0)      NOT NULL CONSTRAINT DF_UserAccount_UpdatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_UserAccount_Role FOREIGN KEY (RoleId) REFERENCES [dbo].[UserRole](Id)
    );
END;

IF OBJECT_ID('[dbo].[TerminalDevice]', 'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[TerminalDevice] (
        [Id]             INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [Name]           NVARCHAR(80)      NOT NULL,
        [DeviceIdentifier] NVARCHAR(100)   NULL,
        [RoleId]         INT               NOT NULL,
        [ApiKey]         NVARCHAR(128)     NOT NULL,
        [BarcodeSecret]  NVARCHAR(128)     NOT NULL,
        [IsActive]       BIT               NOT NULL CONSTRAINT DF_TerminalDevice_IsActive DEFAULT (1),
        [CreatedAt]      DATETIME2(0)      NOT NULL CONSTRAINT DF_TerminalDevice_CreatedAt DEFAULT (SYSUTCDATETIME()),
        [UpdatedAt]      DATETIME2(0)      NOT NULL CONSTRAINT DF_TerminalDevice_UpdatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_TerminalDevice_Role FOREIGN KEY (RoleId) REFERENCES [dbo].[UserRole](Id)
    );
END;

IF OBJECT_ID('[dbo].[TerminalBarcodeSession]', 'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[TerminalBarcodeSession] (
        [Id]           INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [DeviceId]     INT               NOT NULL,
        [UserId]       INT               NULL,
        [Token]        NVARCHAR(120)     NOT NULL,
        [ExpiresAt]    DATETIME2(0)      NOT NULL,
        [UsedAt]       DATETIME2(0)      NULL,
        [CreatedAt]    DATETIME2(0)      NOT NULL CONSTRAINT DF_TerminalBarcodeSession_CreatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_TerminalBarcodeSession_Device FOREIGN KEY (DeviceId) REFERENCES [dbo].[TerminalDevice](Id),
        CONSTRAINT FK_TerminalBarcodeSession_User FOREIGN KEY (UserId) REFERENCES [dbo].[UserAccount](Id)
    );
    CREATE UNIQUE INDEX UX_TerminalBarcodeSession_Token ON [dbo].[TerminalBarcodeSession]([Token]);
END;
