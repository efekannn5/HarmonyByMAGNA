/*
  Migration: Add Admin Role Support to ForkliftLoginSession
  
  Purpose: Support admin users in Android app
  - Add IsAdmin column to identify admin users
  - Add Role column to define user role (admin, forklift, operator, etc.)
  - Update existing sessions with default values
  
  Related: Android API Requirements v1.1.0
  Date: 2025-12-23
*/

-- Add IsAdmin column
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.ForkliftLoginSession') 
    AND name = 'IsAdmin'
)
BEGIN
    ALTER TABLE [dbo].[ForkliftLoginSession]
    ADD [IsAdmin] BIT NOT NULL CONSTRAINT DF_ForkliftLoginSession_IsAdmin DEFAULT (0);
    
    PRINT 'Added IsAdmin column to ForkliftLoginSession';
END
ELSE
BEGIN
    PRINT 'IsAdmin column already exists in ForkliftLoginSession';
END;
GO

-- Add Role column
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.ForkliftLoginSession') 
    AND name = 'Role'
)
BEGIN
    ALTER TABLE [dbo].[ForkliftLoginSession]
    ADD [Role] NVARCHAR(20) NOT NULL CONSTRAINT DF_ForkliftLoginSession_Role DEFAULT ('forklift');
    
    PRINT 'Added Role column to ForkliftLoginSession';
END
ELSE
BEGIN
    PRINT 'Role column already exists in ForkliftLoginSession';
END;
GO

-- Create index for role-based queries (performance optimization)
IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE object_id = OBJECT_ID('dbo.ForkliftLoginSession') 
    AND name = 'IX_ForkliftLoginSession_Role'
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_ForkliftLoginSession_Role
        ON [dbo].[ForkliftLoginSession] ([Role], [IsActive])
        INCLUDE ([OperatorBarcode], [OperatorName]);
    
    PRINT 'Created index IX_ForkliftLoginSession_Role';
END;
GO

-- Update existing sessions with default values (if any active sessions exist)
UPDATE [dbo].[ForkliftLoginSession]
SET IsAdmin = 0, 
    Role = 'forklift'
WHERE IsAdmin IS NULL OR Role IS NULL;

PRINT 'Updated existing ForkliftLoginSession records with default role values';
GO

-- Sample data: Mark specific barcodes as admin (CUSTOMIZE THIS)
-- Uncomment and update with actual admin barcodes
/*
UPDATE [dbo].[ForkliftLoginSession]
SET IsAdmin = 1,
    Role = 'admin'
WHERE OperatorBarcode IN ('ADMIN001', 'ADMIN002', 'ADMIN123');

PRINT 'Marked admin users in ForkliftLoginSession';
*/

-- Create helper view for active admin sessions
IF OBJECT_ID('dbo.vw_ActiveAdminSessions', 'V') IS NOT NULL
    DROP VIEW dbo.vw_ActiveAdminSessions;
GO

CREATE VIEW dbo.vw_ActiveAdminSessions
AS
SELECT 
    Id,
    OperatorBarcode,
    OperatorName,
    DeviceId,
    Role,
    IsAdmin,
    LoginAt,
    ExpiresAt,
    LastActivityAt
FROM [dbo].[ForkliftLoginSession]
WHERE IsActive = 1 
  AND IsAdmin = 1
  AND ExpiresAt > SYSUTCDATETIME();
GO

PRINT 'Created vw_ActiveAdminSessions view';

-- Create helper view for role statistics
IF OBJECT_ID('dbo.vw_ForkliftSessionStats', 'V') IS NOT NULL
    DROP VIEW dbo.vw_ForkliftSessionStats;
GO

CREATE VIEW dbo.vw_ForkliftSessionStats
AS
SELECT 
    Role,
    COUNT(*) as TotalSessions,
    SUM(CASE WHEN IsActive = 1 THEN 1 ELSE 0 END) as ActiveSessions,
    SUM(CASE WHEN IsAdmin = 1 THEN 1 ELSE 0 END) as AdminSessions,
    MAX(LoginAt) as LastLogin
FROM [dbo].[ForkliftLoginSession]
GROUP BY Role;
GO

PRINT 'Created vw_ForkliftSessionStats view';
PRINT 'Migration 014 completed successfully';
PRINT '';
PRINT '⚠️  IMPORTANT: Update admin user barcodes in the script if needed';
PRINT '    Example: OperatorBarcode IN (''ADMIN001'', ''ADMIN002'')';
PRINT '';
PRINT '✅ Next Steps:';
PRINT '    1. Run this migration on database';
PRINT '    2. Update ForkliftLoginSession model in Python';
PRINT '    3. Update /api/forklift/login endpoint';
PRINT '    4. Test admin login flow';
