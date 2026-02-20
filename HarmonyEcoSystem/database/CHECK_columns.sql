-- ============================================
-- DollyEOLInfo ve DollySubmissionHold Kolon Kontrol
-- ============================================

-- DollyEOLInfo kolonları
PRINT '📋 DollyEOLInfo Kolonları:';
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'DollyEOLInfo'
ORDER BY ORDINAL_POSITION;

PRINT '';
PRINT '📋 DollySubmissionHold Kolonları:';
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'DollySubmissionHold'
ORDER BY ORDINAL_POSITION;

PRINT '';
PRINT '📊 DollySubmissionHold - Mevcut Kayıtlar:';
SELECT TOP 5
    Id, DollyNo, VinNo, Status, PartNumber, CustomerReferans, EOLName, TerminalUser
FROM DollySubmissionHold
ORDER BY CreatedAt DESC;
