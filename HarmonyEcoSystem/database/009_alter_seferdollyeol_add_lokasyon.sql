-- Add Lokasyon column to SeferDollyEOL for GHZNA default

IF NOT EXISTS (
    SELECT *
    FROM sys.columns
    WHERE object_id = OBJECT_ID('[dbo].[SeferDollyEOL]')
      AND name = 'Lokasyon'
)
BEGIN
    ALTER TABLE [dbo].[SeferDollyEOL]
    ADD [Lokasyon] NVARCHAR(50) NULL CONSTRAINT DF_SeferDollyEOL_Lokasyon DEFAULT ('GHZNA');

    PRINT 'Added Lokasyon column with default GHZNA to SeferDollyEOL.';
END
