/*
  Migration: Add Barcode Support to UserAccount
  
  Purpose: Allow admin to assign barcodes to users via web panel
  - Add Barcode column to UserAccount table
  - Update admin panel to manage user barcodes
  - Link UserAccount barcode with ForkliftLoginSession
  
  Related: Admin Panel User Management
  Date: 2025-12-23
*/

-- Add Barcode column to UserAccount
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.UserAccount') 
    AND name = 'Barcode'
)
BEGIN
    ALTER TABLE [dbo].[UserAccount]
    ADD [Barcode] NVARCHAR(50) NULL;
    
    PRINT 'Added Barcode column to UserAccount';
END
ELSE
BEGIN
    PRINT 'Barcode column already exists in UserAccount';
END;
GO

-- Create unique index for barcode lookup
IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE object_id = OBJECT_ID('dbo.UserAccount') 
    AND name = 'IX_UserAccount_Barcode'
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX IX_UserAccount_Barcode
        ON [dbo].[UserAccount] ([Barcode])
        WHERE Barcode IS NOT NULL;
    
    PRINT 'Created unique index IX_UserAccount_Barcode';
END;
GO

-- Sample admin barcode assignments (CUSTOMIZE THIS)
/*
UPDATE [dbo].[UserAccount]
SET Barcode = 'ADMIN001'
WHERE Username = 'admin';

UPDATE [dbo].[UserAccount]
SET Barcode = 'ADMIN002'
WHERE Username = 'superuser';

PRINT 'Updated admin user barcodes';
*/

PRINT 'Migration 015 completed successfully';
PRINT '';
PRINT '⚠️  IMPORTANT: Assign barcodes to users via admin panel';
PRINT '    Navigate to: Admin > Kullanıcı Yönetimi';
PRINT '    Edit user and add barcode (e.g., ADMIN001, EMP12345)';
