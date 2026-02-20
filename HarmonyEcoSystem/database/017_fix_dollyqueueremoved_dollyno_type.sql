-- Fix DollyQueueRemoved.DollyNo column type from INT to VARCHAR(20)
-- DollyEOLInfo.DollyNo is VARCHAR(20) so archive table must match

USE [dollydb_test];
GO

-- Step 1: Add new column with correct type
ALTER TABLE DollyQueueRemoved
ADD DollyNo_New VARCHAR(20) NULL;
GO

-- Step 2: Copy data from old column to new (convert int to string)
UPDATE DollyQueueRemoved
SET DollyNo_New = CAST(DollyNo AS VARCHAR(20));
GO

-- Step 3: Drop old column
ALTER TABLE DollyQueueRemoved
DROP COLUMN DollyNo;
GO

-- Step 4: Rename new column to original name
EXEC sp_rename 'DollyQueueRemoved.DollyNo_New', 'DollyNo', 'COLUMN';
GO

-- Step 5: Set NOT NULL constraint
ALTER TABLE DollyQueueRemoved
ALTER COLUMN DollyNo VARCHAR(20) NOT NULL;
GO

PRINT '✅ DollyQueueRemoved.DollyNo column type fixed: INT → VARCHAR(20)';
