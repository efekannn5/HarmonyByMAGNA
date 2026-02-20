IF COL_LENGTH('dbo.DollyGroupEOL', 'ShippingTag') IS NULL
BEGIN
    ALTER TABLE [dbo].[DollyGroupEOL]
    ADD [ShippingTag] NVARCHAR(20) NOT NULL
        CONSTRAINT DF_DollyGroupEOL_ShippingTag DEFAULT ('both');
END;
