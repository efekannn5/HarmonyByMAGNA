/*
Migration 023: Fix SeferDollyEOL date fields that were overwritten by ASN/İrsaliye timestamps.

Problem:
- Bazı SeferDollyEOL kayıtlarında TerminalDate ve/veya EOLDate, gerçek tarama/üretim zamanları yerine
  ASNDate veya IrsaliyeDate (gönderim anı) ile aynı görünüyor.

Approach:
- TerminalDate'i, varsa DollySubmissionHold.LoadingCompletedAt'e; yoksa DollySubmissionHold.CreatedAt'e;
  bunlar yoksa mevcut TerminalDate bırak.
- EOLDate'i, varsa DollyEOLInfo.InsertedAt'e; yoksa DollyEOLInfo.EOLDATE'e; yoksa DollySubmissionHold.CreatedAt'e;
  bunlar yoksa mevcut EOLDate bırak.

Safety:
- Sadece mevcut değerleri daha güvenilir kaynaklarla güncelliyoruz; NULL olmayan mevcut değerler,
  yalnızca alternatif kaynak varsa değişir (COALESCE).
- WHERE filtresi ile etki alanı dar: SeferDollyEOL kayıtları.
- T-SQL, SQL Server için.
*/

SET NOCOUNT ON;

PRINT '🔍 Updating SeferDollyEOL dates from source tables...';

UPDATE s
SET
    TerminalDate = COALESCE(h.LoadingCompletedAt, h.CreatedAt, s.TerminalDate),
    EOLDate      = COALESCE(e.InsertedAt, e.EOLDATE, h.CreatedAt, s.EOLDate)
FROM SeferDollyEOL AS s
LEFT JOIN DollySubmissionHold AS h
    ON s.DollyNo = h.DollyNo AND s.VinNo = h.VinNo
LEFT JOIN DollyEOLInfo AS e
    ON s.DollyNo = e.DollyNo AND s.VinNo = e.VinNo;

PRINT '✅ SeferDollyEOL dates updated.';
