"""
Manager Dashboard Backend - VIEW Based Queries
All queries use SQL Views for clean, efficient data access
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
from typing import Optional, List
from pydantic import BaseModel


# =====================================================
# PYDANTIC MODELS
# =====================================================

class SummaryStats(BaseModel):
    total_sefer: int = 0
    total_dolly: int = 0
    total_vin: int = 0
    total_adet: int = 0
    avg_duration_min: Optional[float] = None
    min_duration_min: Optional[float] = None
    max_duration_min: Optional[float] = None


class GroupPerformanceItem(BaseModel):
    group_name: str
    part_count: int = 0
    dolly_count: int = 0
    sefer_count: int = 0
    vin_count: int = 0
    total_adet: int = 0
    avg_duration_min: Optional[float] = None
    min_duration_min: Optional[float] = None
    max_duration_min: Optional[float] = None


class OperatorItem(BaseModel):
    operator_name: str
    sefer_count: int = 0
    dolly_count: int = 0
    vin_count: int = 0
    total_adet: int = 0
    avg_duration_min: Optional[float] = None
    fastest_min: Optional[float] = None
    slowest_min: Optional[float] = None


class SeferItem(BaseModel):
    sefer_numarasi: Optional[str] = None
    plaka_no: Optional[str] = None
    forklift_operator: Optional[str] = None
    dolly_count: int = 0
    vin_count: int = 0
    total_adet: int = 0
    okutma_suresi_min: Optional[float] = None
    bekleme_suresi_min: Optional[float] = None
    toplam_sure_min: Optional[float] = None
    islem_tarihi: Optional[str] = None
    vardiya: Optional[int] = None


class PartItem(BaseModel):
    part_number: str
    group_name: Optional[str] = None
    eol_name: Optional[str] = None
    dolly_count: int = 0
    vin_count: int = 0
    total_adet: int = 0
    avg_duration_min: Optional[float] = None
    min_duration_min: Optional[float] = None
    max_duration_min: Optional[float] = None


class HourlyItem(BaseModel):
    saat: int
    vardiya: int
    sefer_count: int = 0
    dolly_count: int = 0
    vin_count: int = 0
    total_adet: int = 0


class DollyItem(BaseModel):
    dolly_no: str
    vin_no: Optional[str] = None
    part_number: Optional[str] = None
    group_name: Optional[str] = None
    sefer_numarasi: Optional[str] = None
    plaka_no: Optional[str] = None
    forklift_operator: Optional[str] = None
    eol_to_terminal_min: Optional[float] = None
    terminal_to_asn_min: Optional[float] = None
    toplam_sure_min: Optional[float] = None
    islem_tarihi: Optional[str] = None
    vardiya: Optional[int] = None


class EOLDistributionItem(BaseModel):
    """EOL bazında dağılım (pasta grafik için)"""
    eol_name: str
    total_adet: int = 0
    dolly_count: int = 0
    vin_count: int = 0
    avg_duration_min: Optional[float] = None  # Ortalama doldurma süresi


class DataEntryOperatorItem(BaseModel):
    """Veri girişçi istatistikleri"""
    operator_name: str
    sefer_count: int = 0
    dolly_count: int = 0
    vin_count: int = 0
    total_adet: int = 0
    avg_duration_min: Optional[float] = None


class ShipmentItem(BaseModel):
    """Sevcikyat detayları (SeferDollyEOL bazlı)"""
    gonderim_tarihi: Optional[str] = None
    dolly_count: int = 0
    part_number: Optional[str] = None
    group_name: Optional[str] = None
    eol_names: Optional[str] = None
    plaka_no: Optional[str] = None
    sefer_no: Optional[str] = None
    loading_start: Optional[str] = None
    submit_date: Optional[str] = None
    doc_date: Optional[str] = None
    loading_duration_min: Optional[float] = None
    process_duration_min: Optional[float] = None,
    vardiya: Optional[int] = None


class DashboardData(BaseModel):
    summary: SummaryStats
    group_performance: List[GroupPerformanceItem]
    eol_distribution: List[EOLDistributionItem]
    forklift_operators: List[OperatorItem]
    data_entry_operators: List[DataEntryOperatorItem]
    sefer_list: List[SeferItem]
    part_analysis: List[PartItem]
    hourly_throughput: List[HourlyItem]
    dolly_details: List[DollyItem]
    shipment_details: List[ShipmentItem] = []


# =====================================================
# VIEW-BASED QUERY FUNCTIONS
# =====================================================

def get_summary_stats(db: Session, start_date: date, end_date: date, shift: int = None, min_vin: int = None, hat: str = None) -> SummaryStats:
    """VW_DailySummary veya VW_DollyProcessTimeline'dan özet istatistikler"""
    shift_filter = f"AND Vardiya = {shift}" if shift else ""
    vin_filter = f"AND ToplamVIN >= {min_vin}" if min_vin else ""
    hat_filter = f"AND EOLName = :hat" if hat else ""
    
    # Eğer hat filtresi varsa VW_DollyProcessTimeline üzerinden hesapla (DailySummary'de hat bilgisi yok)
    if hat:
        # VinCount is the core column in VW_DollyProcessTimeline
        hat_vin_filter = f"AND VinCount >= {min_vin}" if min_vin else ""
        query = text(f"""
            SELECT 
                COUNT(DISTINCT SeferNumarasi) as total_sefer,
                COUNT(DISTINCT DollyNo) as total_dolly,
                SUM(VinCount) as total_vin,
                SUM(Adet) as total_adet,
                AVG(CAST(ToplamSure_Min AS FLOAT)) as avg_duration,
                MIN(ToplamSure_Min) as min_duration,
                MAX(ToplamSure_Min) as max_duration
            FROM VW_DollyProcessTimeline WITH (NOLOCK)
            WHERE IslemTarihi BETWEEN :start_date AND :end_date
            {shift_filter}
            {hat_vin_filter}
            {hat_filter}
        """)
    else:
        query = text(f"""
            SELECT 
                COALESCE(SUM(ToplamSefer), 0) as total_sefer,
                COALESCE(SUM(ToplamDolly), 0) as total_dolly,
                COALESCE(SUM(ToplamVIN), 0) as total_vin,
                COALESCE(SUM(ToplamAdet), 0) as total_adet,
                AVG(OrtToplamSure_Min) as avg_duration,
                MIN(EnHizliSure_Min) as min_duration,
                MAX(EnYavasSure_Min) as max_duration
            FROM VW_DailySummary WITH (NOLOCK)
            WHERE IslemTarihi BETWEEN :start_date AND :end_date
            {shift_filter}
            {vin_filter}
        """)
    
    params = {"start_date": start_date, "end_date": end_date}
    if hat: params["hat"] = hat
    
    row = db.execute(query, params).fetchone()
    
    return SummaryStats(
        total_sefer=row.total_sefer or 0,
        total_dolly=row.total_dolly or 0,
        total_vin=row.total_vin or 0,
        total_adet=row.total_adet or 0,
        avg_duration_min=round(row.avg_duration, 1) if row.avg_duration else None,
        min_duration_min=row.min_duration,
        max_duration_min=row.max_duration
    )


def get_group_performance(db: Session, start_date: date, end_date: date, shift: int = None, min_vin: int = None, hat: str = None) -> List[GroupPerformanceItem]:
    """VW_DollyProcessTimeline'dan grup performansı"""
    shift_filter = f"AND Vardiya = {shift}" if shift else ""
    vin_filter = f"AND VinCount >= {min_vin}" if min_vin else ""
    hat_filter = f"AND EOLName = :hat" if hat else ""
    
    query = text(f"""
        SELECT 
            GroupName as group_name,
            COUNT(DISTINCT PartNumber) as part_count,
            COUNT(DISTINCT DollyNo) as dolly_count,
            COUNT(DISTINCT SeferNumarasi) as sefer_count,
            COUNT(*) as vin_count,
            SUM(Adet) as total_adet,
            AVG(CAST(ToplamSure_Min AS FLOAT)) as avg_duration,
            MIN(ToplamSure_Min) as min_duration,
            MAX(ToplamSure_Min) as max_duration
        FROM VW_DollyProcessTimeline WITH (NOLOCK)
        WHERE IslemTarihi BETWEEN :start_date AND :end_date
        {shift_filter}
        {vin_filter}
        {hat_filter}
        GROUP BY GroupName
        ORDER BY total_adet DESC
    """)
    
    params = {"start_date": start_date, "end_date": end_date}
    if hat: params["hat"] = hat
    results = db.execute(query, params).fetchall()
    
    return [GroupPerformanceItem(
        group_name=r.group_name or 'Diğer',
        part_count=r.part_count or 0,
        dolly_count=r.dolly_count or 0,
        sefer_count=r.sefer_count or 0,
        vin_count=r.vin_count or 0,
        total_adet=r.total_adet or 0,
        avg_duration_min=round(r.avg_duration, 1) if r.avg_duration else None,
        min_duration_min=r.min_duration,
        max_duration_min=r.max_duration
    ) for r in results]


def get_operator_stats(db: Session, start_date: date, end_date: date, shift: int = None, min_vin: int = None, hat: str = None) -> List[OperatorItem]:
    """Forklift operatör istatistikleri"""
    shift_filter = ""
    if shift:
        shift_filter = f"""AND CASE 
            WHEN CAST(TerminalDate AS TIME) < '08:00:00' THEN 1
            WHEN CAST(TerminalDate AS TIME) >= '08:00:00' AND CAST(TerminalDate AS TIME) < '16:00:00' THEN 2
            ELSE 3 END = {shift}"""
    
    hat_filter = "AND EOLName = :hat" if hat else ""
    
    params = {"start_date": start_date, "end_date": end_date}
    if hat: params["hat"] = hat

    # Ana sorgu: Operatör bazında özet
    main_query = text(f"""
        SELECT TOP 15
            TerminalUser as operator_name,
            COUNT(DISTINCT SeferNumarasi) as sefer_count,
            COUNT(DISTINCT DollyNo) as dolly_count,
            COUNT(DISTINCT VinNo) as vin_count,
            SUM(ISNULL(Adet, 1)) as total_adet
        FROM SeferDollyEOL WITH (NOLOCK)
        WHERE TerminalDate BETWEEN :start_date AND DATEADD(DAY, 1, :end_date)
           AND TerminalUser IS NOT NULL
          {shift_filter}
          {hat_filter}
        GROUP BY TerminalUser
        ORDER BY total_adet DESC
    """)
    
    main_results = db.execute(main_query, params).fetchall()
    
    # Süre hesaplama: Part toplama süresi (ilk terminal → son terminal)
    duration_query = text(f"""
        SELECT 
            operator_name,
            CAST(AVG(CAST(part_suresi AS FLOAT)) AS DECIMAL(10,1)) as avg_duration,
            MIN(CASE WHEN part_suresi > 0 THEN part_suresi ELSE NULL END) as fastest,
            MAX(part_suresi) as slowest
        FROM (
            SELECT 
                MAX(TerminalUser) as operator_name,
                PartNumber,
                DATEDIFF(MINUTE, MIN(TerminalDate), MAX(TerminalDate)) as part_suresi
            FROM SeferDollyEOL WITH (NOLOCK)
            WHERE TerminalDate BETWEEN :start_date AND DATEADD(DAY, 1, :end_date)
              AND TerminalUser IS NOT NULL
              AND PartNumber IS NOT NULL
              {shift_filter}
            GROUP BY PartNumber
            HAVING DATEDIFF(MINUTE, MIN(TerminalDate), MAX(TerminalDate)) >= 0
               AND DATEDIFF(MINUTE, MIN(TerminalDate), MAX(TerminalDate)) < 480
        ) sub
        GROUP BY operator_name
    """)
    
    duration_results = db.execute(duration_query, {"start_date": start_date, "end_date": end_date}).fetchall()
    
    # Süreleri dict'e dönüştür
    duration_map = {r.operator_name: {
        'avg': float(r.avg_duration) if r.avg_duration else None,
        'fastest': r.fastest,
        'slowest': r.slowest
    } for r in duration_results}
    
    return [OperatorItem(
        operator_name=r.operator_name or 'Bilinmiyor',
        sefer_count=r.sefer_count or 0,
        dolly_count=r.dolly_count or 0,
        vin_count=r.vin_count or 0,
        total_adet=r.total_adet or 0,
        avg_duration_min=duration_map.get(r.operator_name, {}).get('avg'),
        fastest_min=duration_map.get(r.operator_name, {}).get('fastest'),
        slowest_min=duration_map.get(r.operator_name, {}).get('slowest')
    ) for r in main_results]









def get_sefer_list(db: Session, start_date: date, end_date: date, shift: int = None, limit: int = 30, min_vin: int = None, hat: str = None) -> List[SeferItem]:
    """VW_SeferSummary'den sefer listesi"""
    shift_filter = f"AND Vardiya = {shift}" if shift else ""
    vin_filter = f"AND ToplamVIN >= {min_vin}" if min_vin else ""
    hat_filter = "AND SeferNumarasi IN (SELECT DISTINCT SeferNumarasi FROM VW_DollyProcessTimeline WITH (NOLOCK) WHERE EOLName = :hat AND IslemTarihi BETWEEN :start_date AND :end_date)" if hat else ""
    
    query = text(f"""
        SELECT TOP (:limit)
            SeferNumarasi as sefer_numarasi,
            PlakaNo as plaka_no,
            ForkliftOperator as forklift_operator,
            ToplamDolly as dolly_count,
            ToplamVIN as vin_count,
            ToplamAdet as total_adet,
            OkutmaSuresi_Min as okutma_suresi,
            BeklemeSuresi_Min as bekleme_suresi,
            ToplamSure_Min as toplam_sure,
            CONVERT(VARCHAR, IslemTarihi, 23) as islem_tarihi,
            Vardiya as vardiya
        FROM VW_SeferSummary WITH (NOLOCK)
        WHERE IslemTarihi BETWEEN :start_date AND :end_date
        {shift_filter}
        {vin_filter}
        {hat_filter}
        ORDER BY IlkOkutma DESC
    """)
    
    params = {"start_date": start_date, "end_date": end_date, "limit": limit}
    if hat: params["hat"] = hat
    results = db.execute(query, params).fetchall()
    
    return [SeferItem(
        sefer_numarasi=r.sefer_numarasi or None,
        plaka_no=r.plaka_no,
        forklift_operator=r.forklift_operator,
        dolly_count=r.dolly_count or 0,
        vin_count=r.vin_count or 0,
        total_adet=r.total_adet or 0,
        okutma_suresi_min=r.okutma_suresi,
        bekleme_suresi_min=r.bekleme_suresi,
        toplam_sure_min=r.toplam_sure,
        islem_tarihi=r.islem_tarihi,
        vardiya=r.vardiya
    ) for r in results]


def get_part_analysis(db: Session, start_date: date, end_date: date, shift: int = None, min_vin: int = None, hat: str = None) -> List[PartItem]:
    """VW_DollyProcessTimeline'dan parça analizi"""
    shift_filter = f"AND Vardiya = {shift}" if shift else ""
    vin_filter = f"AND VinCount >= {min_vin}" if min_vin else ""
    hat_filter = f"AND EOLName = :hat" if hat else ""
    
    query = text(f"""
        SELECT TOP 50
            PartNumber as part_number,
            MAX(GroupName) as group_name,
            MAX(EOLName) as eol_name,
            COUNT(DISTINCT DollyNo) as dolly_count,
            COUNT(*) as vin_count,
            SUM(Adet) as total_adet,
            AVG(CAST(ToplamSure_Min AS FLOAT)) as avg_duration,
            MIN(ToplamSure_Min) as min_duration,
            MAX(ToplamSure_Min) as max_duration
        FROM VW_DollyProcessTimeline WITH (NOLOCK)
        WHERE IslemTarihi BETWEEN :start_date AND :end_date
          AND PartNumber IS NOT NULL
        {shift_filter}
        {vin_filter}
        {hat_filter}
        GROUP BY PartNumber
        ORDER BY total_adet DESC
    """)
    
    params = {"start_date": start_date, "end_date": end_date}
    if hat: params["hat"] = hat
    results = db.execute(query, params).fetchall()
    
    return [PartItem(
        part_number=r.part_number or 'Bilinmiyor',
        group_name=r.group_name,
        eol_name=r.eol_name,
        dolly_count=r.dolly_count or 0,
        vin_count=r.vin_count or 0,
        total_adet=r.total_adet or 0,
        avg_duration_min=round(r.avg_duration, 1) if r.avg_duration else None,
        min_duration_min=r.min_duration,
        max_duration_min=r.max_duration
    ) for r in results]


def get_hourly_throughput(db: Session, start_date: date, end_date: date, shift: int = None, hat: str = None) -> List[HourlyItem]:
    """VW_HourlyThroughput'dan saatlik verimlilik (Tarih aralığı bazlı, 24 saat doldurularak)"""
    shift_filter = f"AND Vardiya = {shift}" if shift else ""
    hat_filter = f"AND EOLName = :hat" if hat else ""
    
    query = text(f"""
        SELECT 
            Saat as saat,
            SUM(SeferSayisi) as sefer_count,
            SUM(DollySayisi) as dolly_count,
            SUM(VINSayisi) as vin_count,
            SUM(ToplamAdet) as total_adet
        FROM VW_HourlyThroughput WITH (NOLOCK)
        WHERE Tarih BETWEEN :start_date AND :end_date
        {shift_filter}
        {hat_filter}
        GROUP BY Saat
        ORDER BY Saat ASC
    """)
    
    params = {"start_date": start_date, "end_date": end_date}
    if hat: params["hat"] = hat
    db_results = db.execute(query, params).fetchall()
    results_map = {r.saat: r for r in db_results}
    
    padded_results = []
    for h in range(24):
        if h in results_map:
            r = results_map[h]
            padded_results.append(HourlyItem(
                saat=r.saat,
                vardiya=0, # Aggregate görünümde vardiya belirsiz
                sefer_count=r.sefer_count or 0,
                dolly_count=r.dolly_count or 0,
                vin_count=r.vin_count or 0,
                total_adet=r.total_adet or 0
            ))
        else:
            padded_results.append(HourlyItem(
                saat=h,
                vardiya=0,
                sefer_count=0,
                dolly_count=0,
                vin_count=0,
                total_adet=0
            ))
            
    return padded_results



def get_dolly_details(db: Session, start_date: date, end_date: date, shift: int = None, limit: int = 200, min_vin: int = None, hat: str = None) -> List[DollyItem]:
    """VW_DollyProcessTimeline'dan dolly detayları (dolly bazlı aggregate)"""
    shift_filter = f"AND Vardiya = {shift}" if shift else ""
    vin_filter = f"AND VinCount >= {min_vin}" if min_vin else ""
    hat_filter = "AND SeferNumarasi IN (SELECT DISTINCT SeferNumarasi FROM VW_DollyProcessTimeline WITH (NOLOCK) WHERE EOLName = :hat AND IslemTarihi BETWEEN :start_date AND :end_date)" if hat else ""
    
    query = text(f"""
        SELECT TOP (:limit)
            DollyNo as dolly_no,
            VinCount as vin_count,
            PartNumber as part_number,
            GroupName as group_name,
            SeferNumarasi as sefer_numarasi,
            PlakaNo as plaka_no,
            ForkliftOperator as forklift_operator,
            EOL_To_Terminal_Min as eol_to_terminal,
            Terminal_To_ASN_Min as terminal_to_asn,
            ToplamSure_Min as toplam_sure,
            CONVERT(VARCHAR, IslemTarihi, 23) as islem_tarihi,
            Vardiya as vardiya
        FROM VW_DollyProcessTimeline WITH (NOLOCK)
        WHERE IslemTarihi BETWEEN :start_date AND :end_date
        {shift_filter}
        {vin_filter}
        {hat_filter}
        ORDER BY IslemTarihi DESC, DollyNo DESC
    """)
    
    params = {"start_date": start_date, "end_date": end_date, "limit": limit}
    if hat: params["hat"] = hat
    results = db.execute(query, params).fetchall()
    
    return [DollyItem(
        dolly_no=r.dolly_no or '',
        vin_no=f"{r.vin_count} VIN",  # VinCount'u göster
        part_number=r.part_number,
        group_name=r.group_name,
        sefer_numarasi=r.sefer_numarasi,
        plaka_no=r.plaka_no,
        forklift_operator=r.forklift_operator,
        eol_to_terminal_min=r.eol_to_terminal,
        terminal_to_asn_min=r.terminal_to_asn,
        toplam_sure_min=r.toplam_sure,
        islem_tarihi=r.islem_tarihi,
        vardiya=r.vardiya
    ) for r in results]


def get_eol_distribution(db: Session, start_date: date, end_date: date, shift: int = None, min_vin: int = None, hat: str = None) -> List[EOLDistributionItem]:
    """EOL bazında dağılım (pasta grafik ve tablo için)"""
    shift_filter = f"AND Vardiya = {shift}" if shift else ""
    vin_filter = f"AND VinCount >= {min_vin}" if min_vin else ""
    hat_filter = f"AND EOLName = :hat" if hat else ""
    
    # Ana EOL verileri
    query = text(f"""
        SELECT TOP 15
            EOLName as eol_name,
            SUM(Adet) as total_adet,
            COUNT(DISTINCT DollyNo) as dolly_count,
            SUM(VinCount) as vin_count
        FROM VW_DollyProcessTimeline WITH (NOLOCK)
        WHERE IslemTarihi BETWEEN :start_date AND :end_date
          AND EOLName IS NOT NULL
        {shift_filter}
        {vin_filter}
        {hat_filter}
        GROUP BY EOLName
        ORDER BY total_adet DESC
    """)
    
    params = {"start_date": start_date, "end_date": end_date}
    if hat: params["hat"] = hat
    main_results = db.execute(query, params).fetchall()
    
    # Üretim süresini DollyEOLInfo'dan ayrı hesapla (EOLName bazında)
    duration_query = text("""
        SELECT 
            EOLName,
            CAST(AVG(CAST(UretimSuresi AS FLOAT)) AS DECIMAL(10,1)) as avg_duration
        FROM (
            SELECT 
                MAX(EOLName) AS EOLName,
                DATEDIFF(MINUTE, MIN(InsertedAt), MAX(InsertedAt)) AS UretimSuresi
            FROM DollyEOLInfo WITH (NOLOCK)
            WHERE InsertedAt BETWEEN :start_date AND DATEADD(DAY, 1, :end_date)
              AND EOLName IS NOT NULL
            GROUP BY DollyNo
            HAVING COUNT(DISTINCT VinNo) > 1 AND DATEDIFF(MINUTE, MIN(InsertedAt), MAX(InsertedAt)) > 0
        ) sub
        GROUP BY EOLName
    """)
    
    duration_results = db.execute(duration_query, {"start_date": start_date, "end_date": end_date}).fetchall()
    
    # Süreleri dict'e dönüştür
    duration_map = {r.EOLName: float(r.avg_duration) if r.avg_duration else None for r in duration_results}
    
    return [EOLDistributionItem(
        eol_name=r.eol_name or 'Diğer',
        total_adet=r.total_adet or 0,
        dolly_count=r.dolly_count or 0,
        vin_count=r.vin_count or 0,
        avg_duration_min=duration_map.get(r.eol_name)
    ) for r in main_results]


def get_data_entry_operators(db: Session, start_date: date, end_date: date, shift: int = None, min_vin: int = None, hat: str = None) -> List[DataEntryOperatorItem]:
    """Veri girişçi istatistikleri
    VW_DollyProcessTimeline kullanılır
    Terminal_To_ASN_Min = Terminal okutma → ASN gönderim süresi
    """
    shift_filter = f"AND Vardiya = {shift}" if shift else ""
    vin_filter = f"AND VinCount >= {min_vin}" if min_vin else ""
    hat_filter = f"AND EOLName = :hat" if hat else ""
    
    query = text(f"""
        SELECT TOP 15
            DataEntryOperator as operator_name,
            COUNT(DISTINCT SeferNumarasi) as sefer_count,
            COUNT(DISTINCT DollyNo) as dolly_count,
            SUM(VinCount) as vin_count,
            SUM(Adet) as total_adet,
            CAST(AVG(CAST(Terminal_To_ASN_Min AS FLOAT)) AS DECIMAL(10,1)) as avg_duration
        FROM VW_DollyProcessTimeline WITH (NOLOCK)
        WHERE IslemTarihi BETWEEN :start_date AND :end_date
          AND DataEntryOperator IS NOT NULL
          AND Terminal_To_ASN_Min != 10
          AND Terminal_To_ASN_Min > 0
          AND Terminal_To_ASN_Min < 300
        {shift_filter}
        {vin_filter}
        {hat_filter}
        GROUP BY DataEntryOperator
        ORDER BY total_adet DESC
    """)
    
    params = {"start_date": start_date, "end_date": end_date}
    if hat: params["hat"] = hat
    results = db.execute(query, params).fetchall()
    
    # Eğer sonuç yoksa, tüm verileri dahil et
    if not results:
        fallback_query = text(f"""
            SELECT TOP 15
                DataEntryOperator as operator_name,
                COUNT(DISTINCT SeferNumarasi) as sefer_count,
                COUNT(DISTINCT DollyNo) as dolly_count,
                SUM(VinCount) as vin_count,
                SUM(Adet) as total_adet,
                CAST(AVG(CAST(Terminal_To_ASN_Min AS FLOAT)) AS DECIMAL(10,1)) as avg_duration
            FROM VW_DollyProcessTimeline WITH (NOLOCK)
            WHERE IslemTarihi BETWEEN :start_date AND :end_date
              AND DataEntryOperator IS NOT NULL
            {shift_filter}
            {vin_filter}
            {hat_filter}
            GROUP BY DataEntryOperator
            ORDER BY total_adet DESC
        """)
        results = db.execute(fallback_query, params).fetchall()
    
    return [DataEntryOperatorItem(
        operator_name=r.operator_name or 'Bilinmiyor',
        sefer_count=r.sefer_count or 0,
        dolly_count=r.dolly_count or 0,
        vin_count=r.vin_count or 0,
        total_adet=r.total_adet or 0,
        avg_duration_min=float(r.avg_duration) if r.avg_duration else None
    ) for r in results]




def get_shipment_details(db: Session, start_date: date, end_date: date, shift: int = None, hat: str = None) -> List[ShipmentItem]:
    """SeferDollyEOL'den detaylı sevkıyat listesi (Tüm kayıtlar ve EOL detayları)"""
    shift_filter = ""
    if shift:
        if shift == 1: shift_filter = "AND CAST(TerminalDate AS TIME) < '08:00:00'"
        elif shift == 2: shift_filter = "AND CAST(TerminalDate AS TIME) BETWEEN '08:00:00' AND '15:59:59'"
        else: shift_filter = "AND CAST(TerminalDate AS TIME) >= '16:00:00'"

    hat_join = ""
    if hat:
        hat_join = """
            JOIN (
                SELECT DISTINCT SeferNumarasi 
                FROM SeferDollyEOL WITH (NOLOCK) 
                WHERE EOLName = :hat 
                  AND CAST(COALESCE(ASNDate, IrsaliyeDate) AS DATE) BETWEEN :start_date AND :end_date
            ) h ON s.SeferNumarasi = h.SeferNumarasi
        """

    query = text(f"""
        WITH BaseData AS (
            SELECT 
                s.SeferNumarasi,
                s.PartNumber,
                s.EOLName,
                s.DollyNo,
                s.PlakaNo,
                s.TerminalDate,
                COALESCE(s.ASNDate, s.IrsaliyeDate) as DocDate,
                CASE 
                    WHEN s.EOLName LIKE 'V710-LLS%' OR s.EOLName LIKE 'V710-MR%' THEN 'V710 Ayna & LLS'
                    WHEN s.EOLName LIKE 'J74-LLS%' OR s.EOLName LIKE 'J74-MR%' THEN 'J74 Ayna & LLS'
                    WHEN s.EOLName LIKE '%ONTAMPON%' OR s.EOLName LIKE '%HLF%' OR s.EOLName LIKE '%BUMPER%' THEN 
                        CASE 
                            WHEN s.EOLName LIKE 'J74%' THEN 'J74 Ontampon & HLF'
                            WHEN s.EOLName LIKE 'V710%' THEN 'V710 Ontampon'
                            ELSE 'Ontampon Diger'
                        END
                    WHEN s.EOLName LIKE '%HEADLAMP%' OR s.EOLName LIKE '%FINISHER%' THEN 'Headlamp Finisher'
                    ELSE 'Diger'
                END AS group_name,
                CASE 
                    WHEN CAST(COALESCE(s.ASNDate, s.IrsaliyeDate) AS TIME) < '08:00:00' THEN 1
                    WHEN CAST(COALESCE(s.ASNDate, s.IrsaliyeDate) AS TIME) >= '08:00:00' AND CAST(COALESCE(s.ASNDate, s.IrsaliyeDate) AS TIME) < '16:00:00' THEN 2
                    ELSE 3
                END AS Vardiya
            FROM SeferDollyEOL s WITH (NOLOCK)
            {hat_join}
            WHERE CAST(COALESCE(s.ASNDate, s.IrsaliyeDate) AS DATE) BETWEEN :start_date AND :end_date
              AND (s.ASNDate IS NOT NULL OR s.IrsaliyeDate IS NOT NULL)
            {shift_filter.replace('TerminalDate', 'COALESCE(s.ASNDate, s.IrsaliyeDate)')}
        ),
        -- NULL SeferNumarasi'ni geçici bir anahtar ile değiştir ki JOIN çalışsın
        BaseDataKeyed AS (
            SELECT 
                b.*,
                COALESCE(b.SeferNumarasi, 'NO_SEFER_' + b.DollyNo) as SeferKey
            FROM BaseData b
        ),
        UniquePlakas AS (
            SELECT PartNumber, STRING_AGG(PlakaNo, ', ') as plaka_list
            FROM (SELECT DISTINCT PartNumber, PlakaNo FROM BaseData WHERE PlakaNo IS NOT NULL AND PlakaNo <> '-') t
            GROUP BY PartNumber
        ),
        UniqueSefers AS (
            SELECT PartNumber, STRING_AGG(SeferNumarasi, ', ') as sefer_list
            FROM (SELECT DISTINCT PartNumber, SeferNumarasi FROM BaseData WHERE SeferNumarasi IS NOT NULL AND SeferNumarasi <> '') t
            GROUP BY PartNumber
        ),
        UniqueGroups AS (
            SELECT PartNumber, STRING_AGG(group_name, ', ') as group_list
            FROM (SELECT DISTINCT PartNumber, group_name FROM BaseData) t
            GROUP BY PartNumber
        ),
        UniqueEOLs AS (
            SELECT PartNumber, STRING_AGG(EOLName, ', ') as eol_list
            FROM (SELECT DISTINCT PartNumber, EOLName FROM BaseData) t
            GROUP BY PartNumber
        ),
        PartMetrics AS (
            SELECT 
                PartNumber,
                COUNT(DISTINCT DollyNo) as dolly_count,
                MIN(TerminalDate) as loading_start,
                MAX(TerminalDate) as submit_date,
                MAX(DocDate) as doc_date,
                MAX(Vardiya) as vardiya_val
            FROM BaseData
            GROUP BY PartNumber
        )
        SELECT 
            m.doc_date as gonderim_tarihi,
            m.dolly_count,
            m.PartNumber as part_number,
            COALESCE(g.group_list, 'Diger') as group_name,
            COALESCE(e.eol_list, '-') as eol_names,
            COALESCE(p.plaka_list, '-') as plaka_no,
            COALESCE(s.sefer_list, '-') as sefer_no,
            m.loading_start,
            m.submit_date,
            m.doc_date,
            DATEDIFF(MINUTE, m.loading_start, m.submit_date) as loading_duration_min,
            DATEDIFF(MINUTE, m.submit_date, m.doc_date) as process_duration_min,
            m.vardiya_val as vardiya
        FROM PartMetrics m
        LEFT JOIN UniqueGroups g ON m.PartNumber = g.PartNumber
        LEFT JOIN UniqueEOLs e ON m.PartNumber = e.PartNumber
        LEFT JOIN UniquePlakas p ON m.PartNumber = p.PartNumber
        LEFT JOIN UniqueSefers s ON m.PartNumber = s.PartNumber
        ORDER BY m.doc_date DESC
    """)

    
    params = {"start_date": start_date, "end_date": end_date}
    if hat: params["hat"] = hat
    results = db.execute(query, params).fetchall()
    
    return [ShipmentItem(
        gonderim_tarihi=r.gonderim_tarihi.strftime('%Y-%m-%d') if r.gonderim_tarihi else '-',
        dolly_count=r.dolly_count or 0,
        part_number=r.part_number,
        group_name=r.group_name,
        eol_names=r.eol_names or '-',
        plaka_no=r.plaka_no or '-',
        sefer_no=r.sefer_no,
        loading_start=r.loading_start.strftime('%H:%M') if r.loading_start else '-',
        submit_date=r.submit_date.strftime('%H:%M') if r.submit_date else '-',
        doc_date=r.doc_date.strftime('%H:%M') if r.doc_date else '-',
        loading_duration_min=float(r.loading_duration_min) if r.loading_duration_min is not None else 0,
        process_duration_min=float(r.process_duration_min) if r.process_duration_min is not None else 0,
        vardiya=r.vardiya
    ) for r in results]


def get_dashboard_data(db: Session, start_date: date, end_date: date, shift: int = None, min_vin: int = None, hat: str = None) -> DashboardData:
    """Tüm dashboard verilerini tek seferde getir"""
    return DashboardData(
        summary=get_summary_stats(db, start_date, end_date, shift, min_vin, hat),
        group_performance=get_group_performance(db, start_date, end_date, shift, min_vin, hat),
        eol_distribution=get_eol_distribution(db, start_date, end_date, shift, min_vin, hat),
        forklift_operators=get_operator_stats(db, start_date, end_date, shift, min_vin, hat),
        data_entry_operators=get_data_entry_operators(db, start_date, end_date, shift, min_vin, hat),
        sefer_list=get_sefer_list(db, start_date, end_date, shift, limit=30, min_vin=min_vin, hat=hat),
        part_analysis=get_part_analysis(db, start_date, end_date, shift, min_vin, hat),
        hourly_throughput=get_hourly_throughput(db, start_date, end_date, shift, hat),
        dolly_details=get_dolly_details(db, start_date, end_date, shift, limit=200, min_vin=min_vin, hat=hat),
        shipment_details=get_shipment_details(db, start_date, end_date, shift, hat)
    )

def get_all_eol_names(db: Session) -> List[str]:
    """Fetch all distinct EOL names for dynamic mapping"""
    try:
        query = text("SELECT DISTINCT EOLName FROM SeferDollyEOL WITH (NOLOCK) WHERE EOLName IS NOT NULL")
        result = db.execute(query).fetchall()
        return [row[0] for row in result if row[0]]
    except Exception as e:
        print(f"Error fetching EOL names: {e}")
        return []
