/*
  Migration: Create ForkliftLoginSession table for Android barcode login
  
  Purpose: Track forklift operator logins via barcode scanning
  - Operators scan their employee barcode to login
  - Session tokens are generated and validated
  - All forklift actions are tracked to specific users
*/

-- Create ForkliftLoginSession table
IF OBJECT_ID('[dbo].[ForkliftLoginSession]', 'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[ForkliftLoginSession] (
        [Id]                INT IDENTITY(1,1)     NOT NULL PRIMARY KEY,
        [OperatorBarcode]   NVARCHAR(50)          NOT NULL,
        [OperatorName]      NVARCHAR(100)         NOT NULL,
        [DeviceId]          NVARCHAR(100)         NULL,          -- Android device identifier
        [SessionToken]      NVARCHAR(128)         NOT NULL,      -- JWT or random token
        [IsActive]          BIT                   NOT NULL CONSTRAINT DF_ForkliftLoginSession_IsActive DEFAULT (1),
        [LoginAt]           DATETIME2(0)          NOT NULL CONSTRAINT DF_ForkliftLoginSession_LoginAt DEFAULT (SYSUTCDATETIME()),
        [LogoutAt]          DATETIME2(0)          NULL,
        [ExpiresAt]         DATETIME2(0)          NOT NULL,      -- Auto-logout after 8 hours
        [LastActivityAt]    DATETIME2(0)          NULL,          -- Track last API call
        [IpAddress]         NVARCHAR(50)          NULL,
        [UserAgent]         NVARCHAR(255)         NULL,
        [Metadata]          NVARCHAR(MAX)         NULL           -- JSON: device info, app version, etc.
    );
    
    PRINT 'Created ForkliftLoginSession table';
END
ELSE
BEGIN
    PRINT 'ForkliftLoginSession table already exists';
END;
GO

-- Create index for fast session token lookup
IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE object_id = OBJECT_ID('dbo.ForkliftLoginSession') 
    AND name = 'IX_ForkliftLoginSession_Token'
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX IX_ForkliftLoginSession_Token
        ON [dbo].[ForkliftLoginSession] ([SessionToken])
        WHERE IsActive = 1;
    
    PRINT 'Created index IX_ForkliftLoginSession_Token';
END;
GO

-- Create index for operator barcode lookup
IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE object_id = OBJECT_ID('dbo.ForkliftLoginSession') 
    AND name = 'IX_ForkliftLoginSession_Barcode'
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_ForkliftLoginSession_Barcode
        ON [dbo].[ForkliftLoginSession] ([OperatorBarcode], [IsActive])
        INCLUDE ([SessionToken], [OperatorName], [ExpiresAt]);
    
    PRINT 'Created index IX_ForkliftLoginSession_Barcode';
END;
GO

-- Create cleanup procedure for expired sessions
IF OBJECT_ID('dbo.sp_CleanupExpiredForkliftSessions', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_CleanupExpiredForkliftSessions;
GO

CREATE PROCEDURE dbo.sp_CleanupExpiredForkliftSessions
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE [dbo].[ForkliftLoginSession]
    SET IsActive = 0,
        LogoutAt = SYSUTCDATETIME()
    WHERE IsActive = 1
      AND ExpiresAt < SYSUTCDATETIME();
    
    SELECT @@ROWCOUNT AS CleanedSessionCount;
END;
GO

PRINT 'Created sp_CleanupExpiredForkliftSessions procedure';
PRINT 'Migration 012 completed successfully';
