IF COL_LENGTH('dbo.DollyEOLInfo', 'EOLDollyBarcode') IS NULL
BEGIN
    ALTER TABLE [dbo].[DollyEOLInfo]
    ADD [EOLDollyBarcode] NVARCHAR(100) NULL;
END;
