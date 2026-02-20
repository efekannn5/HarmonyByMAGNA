"""
Manager Dashboard SQL Queries
All queries use actual database column names and DollySubmissionHold for real-time tracking
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
from models_manager import (
    ProcessDuration,
    ProcessDurationAnalysis,
    ProcessDurationItem,
    HourlyHeatmap,
    DailyPerformance,
    EOLPerformance
)


# ==================== PROCESS DURATION ANALYSIS ====================
def get_process_duration_analysis(db: Session, start_date: date, end_date: date, shift: int = None) -> ProcessDurationAnalysis:
    """
    Analyze process durations across all stages - DOLLY based
    Uses DollySubmissionHold for real-time scan tracking
    """
    
    shift_filter = ""
    if shift:
        if shift == 1:
            shift_filter = "AND CAST(sde.TerminalDate AS TIME) < '08:00:00'"
        elif shift == 2:
            shift_filter = "AND CAST(sde.TerminalDate AS TIME) >= '08:00:00' AND CAST(sde.TerminalDate AS TIME) < '16:00:00'"
        else:
            shift_filter = "AND CAST(sde.TerminalDate AS TIME) >= '16:00:00'"
    
    base_cte = f"""
        WITH DollyProcessData AS (
            SELECT 
                sde.DollyNo,
                COALESCE(sde.PartNumber, dsh.PartNumber) as PartNumber,
                sde.SeferNumarasi,
                dsh.PlakaNo,
                dei.EOLDATE as eol_time,
                dsh.CreatedAt as scan_time,
                dsh.LoadingCompletedAt as loading_completed_time,
                sde.TerminalDate as terminal_time,
                sde.ASNDate as asn_time,
                sde.IrsaliyeDate as irsaliye_time
            FROM SeferDollyEOL sde WITH (NOLOCK)
            LEFT JOIN DollyEOLInfo dei WITH (NOLOCK) ON sde.DollyNo = dei.DollyNo
            LEFT JOIN DollySubmissionHold dsh WITH (NOLOCK) ON sde.DollyNo = dsh.DollyNo
            WHERE CAST(sde.TerminalDate AS DATE) BETWEEN :start_date AND :end_date
            {shift_filter}
        ),
        ProcessDurations AS (
            SELECT 
                DollyNo,
                PartNumber,
                SeferNumarasi,
                PlakaNo,
                CASE 
                    WHEN eol_time IS NOT NULL AND scan_time IS NOT NULL 
                    THEN DATEDIFF(MINUTE, eol_time, scan_time)
                    WHEN eol_time IS NOT NULL AND terminal_time IS NOT NULL
                    THEN DATEDIFF(MINUTE, eol_time, terminal_time)
                    ELSE NULL
                END as wait_before_scan_minutes,
                CASE 
                    WHEN scan_time IS NOT NULL AND loading_completed_time IS NOT NULL 
                    THEN DATEDIFF(MINUTE, scan_time, loading_completed_time)
                    WHEN scan_time IS NOT NULL AND terminal_time IS NOT NULL
                    THEN DATEDIFF(MINUTE, scan_time, terminal_time)
                    ELSE NULL
                END as loading_duration_minutes,
                CASE 
                    WHEN loading_completed_time IS NOT NULL AND terminal_time IS NOT NULL 
                    THEN DATEDIFF(MINUTE, loading_completed_time, terminal_time)
                    WHEN scan_time IS NOT NULL AND terminal_time IS NOT NULL
                    THEN DATEDIFF(MINUTE, scan_time, terminal_time)
                    ELSE NULL
                END as terminal_processing_minutes,
                CASE 
                    WHEN terminal_time IS NOT NULL AND COALESCE(asn_time, irsaliye_time) IS NOT NULL 
                    THEN DATEDIFF(MINUTE, terminal_time, COALESCE(asn_time, irsaliye_time))
                    ELSE NULL
                END as shipment_prep_minutes,
                CASE 
                    WHEN eol_time IS NOT NULL AND COALESCE(asn_time, irsaliye_time) IS NOT NULL 
                    THEN DATEDIFF(MINUTE, eol_time, COALESCE(asn_time, irsaliye_time))
                    WHEN eol_time IS NOT NULL AND terminal_time IS NOT NULL
                    THEN DATEDIFF(MINUTE, eol_time, terminal_time)
                    ELSE NULL
                END as total_minutes
            FROM DollyProcessData
        )
    """

    aggregate_query = text(base_cte + """
        SELECT 
            AVG(CAST(wait_before_scan_minutes AS FLOAT)) as avg_wait_before,
            MIN(wait_before_scan_minutes) as min_wait_before,
            MAX(wait_before_scan_minutes) as max_wait_before,
            AVG(CAST(loading_duration_minutes AS FLOAT)) as avg_loading,
            MIN(loading_duration_minutes) as min_loading,
            MAX(loading_duration_minutes) as max_loading,
            AVG(CAST(terminal_processing_minutes AS FLOAT)) as avg_terminal,
            MIN(terminal_processing_minutes) as min_terminal,
            MAX(terminal_processing_minutes) as max_terminal,
            AVG(CAST(shipment_prep_minutes AS FLOAT)) as avg_shipment,
            MIN(shipment_prep_minutes) as min_shipment,
            MAX(shipment_prep_minutes) as max_shipment,
            AVG(CAST(total_minutes AS FLOAT)) as avg_total,
            MIN(total_minutes) as min_total,
            MAX(total_minutes) as max_total,
            COUNT(DISTINCT DollyNo) as dolly_count
        FROM ProcessDurations
    """)

    detail_query = text(base_cte + """
        SELECT TOP (:limit)
            DollyNo as dolly_no,
            PartNumber as part_number,
            SeferNumarasi as sefer_numarasi,
            PlakaNo as plaka_no,
            wait_before_scan_minutes,
            loading_duration_minutes,
            shipment_prep_minutes,
            total_minutes
        FROM ProcessDurations
        ORDER BY CASE WHEN total_minutes IS NULL THEN 1 ELSE 0 END, total_minutes DESC, DollyNo
    """)

    params = {"start_date": start_date, "end_date": end_date}
    result = db.execute(aggregate_query, params).fetchone()
    detail_rows = db.execute(detail_query, {**params, "limit": 50}).fetchall()

    if not result or result.dolly_count == 0:
        empty_duration = ProcessDuration(
            stage_name="No Data",
            avg_duration_minutes=0,
            min_duration_minutes=0,
            max_duration_minutes=0,
            dolly_count=0
        )
        return ProcessDurationAnalysis(
            production_duration=empty_duration,
            wait_before_scan_duration=empty_duration,
            scanning_duration=empty_duration,
            wait_after_scan_duration=empty_duration,
            total_process_duration=empty_duration,
            items=[]
        )

    items = [
        ProcessDurationItem(
            dolly_no=row.dolly_no,
            part_number=row.part_number,
            sefer_numarasi=row.sefer_numarasi,
            plaka_no=row.plaka_no,
            wait_before_scan_minutes=row.wait_before_scan_minutes,
            loading_duration_minutes=row.loading_duration_minutes,
            shipment_prep_minutes=row.shipment_prep_minutes,
            total_minutes=row.total_minutes,
        )
        for row in detail_rows
    ]

    return ProcessDurationAnalysis(
        production_duration=ProcessDuration(
            stage_name="Uretim (EOL Cikis)",
            avg_duration_minutes=30,
            min_duration_minutes=20,
            max_duration_minutes=45,
            dolly_count=result.dolly_count
        ),
        wait_before_scan_duration=ProcessDuration(
            stage_name="Okutulmadan Bekleme (EOL->Forklift)",
            avg_duration_minutes=result.avg_wait_before or 0,
            min_duration_minutes=result.min_wait_before or 0,
            max_duration_minutes=result.max_wait_before or 0,
            dolly_count=result.dolly_count
        ),
        scanning_duration=ProcessDuration(
            stage_name="Yukleme Islemi (Scan->Loading)",
            avg_duration_minutes=result.avg_loading or 0,
            min_duration_minutes=result.min_loading or 0,
            max_duration_minutes=result.max_loading or 0,
            dolly_count=result.dolly_count
        ),
        wait_after_scan_duration=ProcessDuration(
            stage_name="Sevkiyat Hazirlik (Terminal->ASN/Irsaliye)",
            avg_duration_minutes=result.avg_shipment or 0,
            min_duration_minutes=result.min_shipment or 0,
            max_duration_minutes=result.max_shipment or 0,
            dolly_count=result.dolly_count
        ),
        total_process_duration=ProcessDuration(
            stage_name="Toplam Surec (EOL->Sevkiyat)",
            avg_duration_minutes=result.avg_total or 0,
            min_duration_minutes=result.min_total or 0,
            max_duration_minutes=result.max_total or 0,
            dolly_count=result.dolly_count
        ),
        items=items
    )


# ==================== HOURLY HEATMAP ====================
def get_hourly_heatmap(db: Session, start_date: date, end_date: date) -> list[HourlyHeatmap]:
    """
    Get hourly activity heatmap (24x7 grid) using DollySubmissionHold.CreatedAt
    """
    query = text("""
        SELECT 
            DATEPART(HOUR, CreatedAt) as hour_of_day,
            DATEPART(WEEKDAY, CreatedAt) - 1 as day_of_week,
            COUNT(DISTINCT DollyNo) as dolly_count
        FROM DollySubmissionHold WITH (NOLOCK)
        WHERE CAST(CreatedAt AS DATE) BETWEEN :start_date AND :end_date
        GROUP BY 
            DATEPART(HOUR, CreatedAt),
            DATEPART(WEEKDAY, CreatedAt)
        ORDER BY day_of_week, hour_of_day
    """)
    
    results = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
    
    return [
        HourlyHeatmap(
            hour_of_day=row.hour_of_day,
            day_of_week=row.day_of_week,
            dolly_count=row.dolly_count
        )
        for row in results
    ]


# ==================== DAILY PERFORMANCE ====================
def get_daily_performances(db: Session, start_date: date, end_date: date, shift: int = None) -> list[DailyPerformance]:
    """
    Get daily performance metrics - uses TerminalDate from SeferDollyEOL
    """
    shift_filter = ""
    if shift:
        if shift == 1:
            shift_filter = "AND CAST(TerminalDate AS TIME) >= '08:00:00' AND CAST(TerminalDate AS TIME) < '16:00:00'"
        elif shift == 2:
            shift_filter = "AND CAST(TerminalDate AS TIME) >= '16:00:00'"
        else:
            shift_filter = "AND CAST(TerminalDate AS TIME) >= '00:00:00' AND CAST(TerminalDate AS TIME) < '08:00:00'"
    
    query = text(f"""
        SELECT 
            CAST(TerminalDate AS DATE) as performance_date,
            COUNT(DISTINCT DollyNo) as dolly_count,
            SUM(Adet) as total_quantity,
            COUNT(DISTINCT SeferNumarasi) as sefer_count,
            COUNT(DISTINCT CASE WHEN ASNDate IS NOT NULL THEN DollyNo END) as asn_count,
            COUNT(DISTINCT CASE WHEN IrsaliyeDate IS NOT NULL THEN DollyNo END) as irsaliye_count
        FROM SeferDollyEOL WITH (NOLOCK)
        WHERE CAST(TerminalDate AS DATE) BETWEEN :start_date AND :end_date
        {shift_filter}
        GROUP BY CAST(TerminalDate AS DATE)
        ORDER BY performance_date
    """)
    
    results = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
    
    return [
        DailyPerformance(
            date=row.performance_date,
            dolly_count=row.dolly_count,
            total_quantity=row.total_quantity,
            sefer_count=row.sefer_count,
            asn_completion_rate=(row.asn_count / row.dolly_count * 100) if row.dolly_count > 0 else 0,
            irsaliye_completion_rate=(row.irsaliye_count / row.dolly_count * 100) if row.dolly_count > 0 else 0
        )
        for row in results
    ]


# ==================== EOL PERFORMANCE ====================
def get_eol_performances(db: Session, start_date: date, end_date: date, shift: int = None) -> list[EOLPerformance]:
    """
    Get EOL-based performance metrics
    """
    shift_filter = ""
    if shift:
        if shift == 1:
            shift_filter = "AND CAST(TerminalDate AS TIME) >= '08:00:00' AND CAST(TerminalDate AS TIME) < '16:00:00'"
        elif shift == 2:
            shift_filter = "AND CAST(TerminalDate AS TIME) >= '16:00:00'"
        else:
            shift_filter = "AND CAST(TerminalDate AS TIME) >= '00:00:00' AND CAST(TerminalDate AS TIME) < '08:00:00'"
    
    query = text(f"""
        SELECT 
            EOLName as eol_name,
            COUNT(DISTINCT DollyNo) as dolly_count,
            SUM(Adet) as total_quantity,
            AVG(CAST(Adet AS FLOAT)) as avg_quantity_per_dolly,
            COUNT(DISTINCT SeferNumarasi) as sefer_count,
            COUNT(DISTINCT CASE WHEN ASNDate IS NOT NULL THEN DollyNo END) as asn_count
        FROM SeferDollyEOL WITH (NOLOCK)
        WHERE CAST(TerminalDate AS DATE) BETWEEN :start_date AND :end_date
        {shift_filter}
        GROUP BY EOLName
        ORDER BY dolly_count DESC
    """)
    
    results = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
    
    return [
        EOLPerformance(
            eol_name=row.eol_name or "Unknown",
            dolly_count=row.dolly_count,
            total_quantity=row.total_quantity,
            avg_quantity_per_dolly=round(row.avg_quantity_per_dolly, 2) if row.avg_quantity_per_dolly else 0,
            sefer_count=row.sefer_count,
            asn_completion_rate=(row.asn_count / row.dolly_count * 100) if row.dolly_count > 0 else 0
        )
        for row in results
    ]


# ==================== SUMMARY STATS ====================
def get_summary_stats(db: Session, start_date: date, end_date: date, shift: int = None) -> dict:
    """
    Get overall summary statistics - uses SeferNumarasi instead of SeferNo
    """
    shift_filter = ""
    if shift:
        if shift == 1:
            shift_filter = "AND CAST(TerminalDate AS TIME) >= '08:00:00' AND CAST(TerminalDate AS TIME) < '16:00:00'"
        elif shift == 2:
            shift_filter = "AND CAST(TerminalDate AS TIME) >= '16:00:00'"
        else:
            shift_filter = "AND CAST(TerminalDate AS TIME) >= '00:00:00' AND CAST(TerminalDate AS TIME) < '08:00:00'"
    
    query = text(f"""
        SELECT 
            COUNT(DISTINCT DollyNo) as total_dollies,
            SUM(Adet) as total_quantity,
            COUNT(DISTINCT PartNumber) as unique_part_count,
            COUNT(DISTINCT SeferNumarasi) as total_sefer,
            COUNT(DISTINCT EOLName) as unique_eol_count,
            COUNT(DISTINCT CASE WHEN ASNDate IS NOT NULL THEN DollyNo END) as asn_completed,
            COUNT(DISTINCT CASE WHEN IrsaliyeDate IS NOT NULL THEN DollyNo END) as irsaliye_completed
        FROM SeferDollyEOL WITH (NOLOCK)
        WHERE CAST(TerminalDate AS DATE) BETWEEN :start_date AND :end_date
        {shift_filter}
    """)
    
    result = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchone()
    
    return {
        "total_dollies": result.total_dollies or 0,
        "total_quantity": result.total_quantity or 0,
        "unique_part_count": result.unique_part_count or 0,
        "total_sefer": result.total_sefer or 0,
        "unique_eol_count": result.unique_eol_count or 0,
        "asn_completion_rate": (result.asn_completed / result.total_dollies * 100) if result.total_dollies > 0 else 0,
        "irsaliye_completion_rate": (result.irsaliye_completed / result.total_dollies * 100) if result.total_dollies > 0 else 0
    }


# ==================== PART ANALYSIS ====================
def get_part_analysis(db: Session, start_date: date, end_date: date, shift: int = None) -> list:
    """
    Part bazlı süre analizi - Her PartNumber için ortalama süreler
    EOLName pattern'e göre grup belirleme
    """
    from models_manager import PartAnalysisItem
    
    shift_filter = ""
    if shift:
        if shift == 1:
            shift_filter = "AND CAST(sde.TerminalDate AS TIME) >= '08:00:00' AND CAST(sde.TerminalDate AS TIME) < '16:00:00'"
        elif shift == 2:
            shift_filter = "AND CAST(sde.TerminalDate AS TIME) >= '16:00:00'"
        else:
            shift_filter = "AND CAST(sde.TerminalDate AS TIME) >= '00:00:00' AND CAST(sde.TerminalDate AS TIME) < '08:00:00'"
    
    query = text(f"""
        WITH DollyTimes AS (
            SELECT 
                COALESCE(sde.PartNumber, 'Bilinmiyor') as PartNumber,
                CASE 
                    WHEN sde.EOLName LIKE 'V710-LLS%' OR sde.EOLName LIKE 'V710-MR%' THEN 'V710 Ayna & LLS'
                    WHEN sde.EOLName LIKE 'J74-LLS%' OR sde.EOLName LIKE 'J74-MR%' THEN 'J74 Ayna & LLS'
                    WHEN sde.EOLName LIKE 'J74-ONTAMPON%' OR sde.EOLName LIKE 'J74-HLF%' THEN 'J74 Ontampon & HLF'
                    WHEN sde.EOLName LIKE 'V710-ONTAMPON%' THEN 'V710 Ontampon'
                    ELSE 'Diğer'
                END as GroupName,
                sde.DollyNo,
                sde.Adet,
                sde.EOLDate as eol_time,
                sde.TerminalDate as terminal_time,
                sde.ASNDate as asn_time,
                sde.IrsaliyeDate as irsaliye_time,
                -- Toplam süre (TerminalDate'den IrsaliyeDate'e)
                CASE 
                    WHEN sde.TerminalDate IS NOT NULL AND sde.IrsaliyeDate IS NOT NULL 
                    THEN DATEDIFF(MINUTE, sde.TerminalDate, sde.IrsaliyeDate)
                    ELSE NULL
                END as wait_before_scan,
                -- ASN'den Irsaliye'ye süre
                CASE 
                    WHEN sde.ASNDate IS NOT NULL AND sde.IrsaliyeDate IS NOT NULL
                    THEN DATEDIFF(MINUTE, sde.ASNDate, sde.IrsaliyeDate)
                    ELSE NULL
                END as loading_duration,
                -- Terminal'den ASN'e süre
                CASE 
                    WHEN sde.TerminalDate IS NOT NULL AND sde.ASNDate IS NOT NULL
                    THEN DATEDIFF(MINUTE, sde.TerminalDate, sde.ASNDate)
                    ELSE NULL
                END as terminal_duration,
                -- Toplam süre
                CASE 
                    WHEN sde.TerminalDate IS NOT NULL AND sde.IrsaliyeDate IS NOT NULL 
                    THEN DATEDIFF(MINUTE, sde.TerminalDate, sde.IrsaliyeDate)
                    ELSE NULL
                END as total_minutes
            FROM SeferDollyEOL sde WITH (NOLOCK)
            WHERE CAST(sde.TerminalDate AS DATE) BETWEEN :start_date AND :end_date
            {shift_filter}
        )


        SELECT 
            PartNumber as part_number,
            MAX(GroupName) as group_name,
            COUNT(DISTINCT DollyNo) as dolly_count,
            SUM(ISNULL(Adet, 1)) as total_quantity,
            AVG(CAST(wait_before_scan AS FLOAT)) as avg_wait_before_scan,
            AVG(CAST(loading_duration AS FLOAT)) as avg_loading_duration,
            AVG(CAST(terminal_duration AS FLOAT)) as avg_terminal_duration,
            AVG(CAST(total_minutes AS FLOAT)) as avg_total_duration,
            MIN(total_minutes) as min_total_duration,
            MAX(total_minutes) as max_total_duration
        FROM DollyTimes
        GROUP BY PartNumber
        HAVING COUNT(DISTINCT DollyNo) > 0
        ORDER BY COUNT(DISTINCT DollyNo) DESC
    """)
    
    results = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
    
    return [
        PartAnalysisItem(
            part_number=row.part_number or "Bilinmiyor",
            group_name=row.group_name,
            dolly_count=row.dolly_count or 0,
            total_quantity=row.total_quantity or 0,
            avg_wait_before_scan=round(row.avg_wait_before_scan or 0, 1),
            avg_loading_duration=round(row.avg_loading_duration or 0, 1),
            avg_terminal_duration=round(row.avg_terminal_duration or 0, 1),
            avg_total_duration=round(row.avg_total_duration or 0, 1),
            min_total_duration=row.min_total_duration or 0,
            max_total_duration=row.max_total_duration or 0
        )
        for row in results
    ]


# ==================== GROUP ANALYSIS ====================
def get_group_analysis(db: Session, start_date: date, end_date: date, shift: int = None) -> list:
    """
    DollyGroup bazlı süre analizi - EOLName pattern'e göre grup belirleme
    """
    from models_manager import GroupAnalysisItem
    
    shift_filter = ""
    if shift:
        if shift == 1:
            shift_filter = "AND CAST(sde.TerminalDate AS TIME) >= '08:00:00' AND CAST(sde.TerminalDate AS TIME) < '16:00:00'"
        elif shift == 2:
            shift_filter = "AND CAST(sde.TerminalDate AS TIME) >= '16:00:00'"
        else:
            shift_filter = "AND CAST(sde.TerminalDate AS TIME) >= '00:00:00' AND CAST(sde.TerminalDate AS TIME) < '08:00:00'"
    
    query = text(f"""
        WITH DollyTimes AS (
            SELECT 
                CASE 
                    WHEN sde.EOLName LIKE 'V710-LLS%' OR sde.EOLName LIKE 'V710-MR%' THEN 1
                    WHEN sde.EOLName LIKE 'J74-LLS%' OR sde.EOLName LIKE 'J74-MR%' THEN 2
                    WHEN sde.EOLName LIKE 'J74-ONTAMPON%' OR sde.EOLName LIKE 'J74-HLF%' THEN 3
                    WHEN sde.EOLName LIKE 'V710-ONTAMPON%' THEN 4
                    ELSE 0
                END as GroupId,
                CASE 
                    WHEN sde.EOLName LIKE 'V710-LLS%' OR sde.EOLName LIKE 'V710-MR%' THEN 'V710 Ayna & LLS'
                    WHEN sde.EOLName LIKE 'J74-LLS%' OR sde.EOLName LIKE 'J74-MR%' THEN 'J74 Ayna & LLS'
                    WHEN sde.EOLName LIKE 'J74-ONTAMPON%' OR sde.EOLName LIKE 'J74-HLF%' THEN 'J74 Ontampon & HLF'
                    WHEN sde.EOLName LIKE 'V710-ONTAMPON%' THEN 'V710 Ontampon'
                    ELSE 'Diğer'
                END as GroupName,
                sde.PartNumber,
                sde.DollyNo,
                sde.Adet,
                sde.EOLDate as eol_time,
                sde.TerminalDate as terminal_time,
                sde.ASNDate as asn_time,
                sde.IrsaliyeDate as irsaliye_time,
                -- Toplam süre (TerminalDate'den IrsaliyeDate'e)
                CASE 
                    WHEN sde.TerminalDate IS NOT NULL AND sde.IrsaliyeDate IS NOT NULL 
                    THEN DATEDIFF(MINUTE, sde.TerminalDate, sde.IrsaliyeDate)
                    ELSE NULL
                END as wait_before_scan,
                -- ASN'den Irsaliye'ye süre
                CASE 
                    WHEN sde.ASNDate IS NOT NULL AND sde.IrsaliyeDate IS NOT NULL
                    THEN DATEDIFF(MINUTE, sde.ASNDate, sde.IrsaliyeDate)
                    ELSE NULL
                END as loading_duration,
                -- Terminal'den ASN'e süre
                CASE 
                    WHEN sde.TerminalDate IS NOT NULL AND sde.ASNDate IS NOT NULL
                    THEN DATEDIFF(MINUTE, sde.TerminalDate, sde.ASNDate)
                    ELSE NULL
                END as terminal_duration,
                -- Toplam süre
                CASE 
                    WHEN sde.TerminalDate IS NOT NULL AND sde.IrsaliyeDate IS NOT NULL 
                    THEN DATEDIFF(MINUTE, sde.TerminalDate, sde.IrsaliyeDate)
                    ELSE NULL
                END as total_minutes
            FROM SeferDollyEOL sde WITH (NOLOCK)
            WHERE CAST(sde.TerminalDate AS DATE) BETWEEN :start_date AND :end_date
            {shift_filter}
        )
        SELECT 


            GroupId as group_id,
            GroupName as group_name,
            COUNT(DISTINCT PartNumber) as part_count,
            COUNT(DISTINCT DollyNo) as dolly_count,
            SUM(ISNULL(Adet, 1)) as total_quantity,
            AVG(CAST(wait_before_scan AS FLOAT)) as avg_wait_before_scan,
            AVG(CAST(loading_duration AS FLOAT)) as avg_loading_duration,
            AVG(CAST(terminal_duration AS FLOAT)) as avg_terminal_duration,
            AVG(CAST(total_minutes AS FLOAT)) as avg_total_duration
        FROM DollyTimes
        GROUP BY GroupId, GroupName
        HAVING COUNT(DISTINCT DollyNo) > 0
        ORDER BY COUNT(DISTINCT DollyNo) DESC
    """)
    
    results = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
    
    return [
        GroupAnalysisItem(
            group_id=row.group_id or 0,
            group_name=row.group_name or "Diğer",
            part_count=row.part_count or 0,
            dolly_count=row.dolly_count or 0,
            total_quantity=row.total_quantity or 0,
            avg_wait_before_scan=round(row.avg_wait_before_scan or 0, 1),
            avg_loading_duration=round(row.avg_loading_duration or 0, 1),
            avg_terminal_duration=round(row.avg_terminal_duration or 0, 1),
            avg_total_duration=round(row.avg_total_duration or 0, 1)
        )
        for row in results
    ]


# ==================== DETAILED DOLLY LIST ====================
def get_dolly_details(db: Session, start_date: date, end_date: date, shift: int = None, limit: int = 100) -> list:
    """
    Detaylı dolly listesi - Excel benzeri satır satır görünüm
    EOLName pattern'e göre grup belirleme
    """
    from models_manager import DollyDetailRow
    
    shift_filter = ""
    if shift:
        shift_filter = f"AND Vardiya = {shift}"
    
    # VW_DollyProcessTimeline view kullanarak çok daha basit ve hızlı sorgu
    query = text(f"""
        SELECT TOP (:limit)
            DollyNo as dolly_no,
            VinNo as vin_no,
            COALESCE(PartNumber, 'Bilinmiyor') as part_number,
            GroupName as group_name,
            EOLName as eol_name,
            SeferNumarasi as sefer_numarasi,
            PlakaNo as plaka_no,
            EOLDate as eol_date,
            TerminalOkutmaZamani as terminal_time,
            ASN_GonderimZamani as asn_time,
            Irsaliye_GonderimZamani as irsaliye_time,
            EOL_To_Terminal_Min as wait_before_scan_min,
            Terminal_To_ASN_Min as loading_duration_min,
            Terminal_To_Irsaliye_Min as terminal_duration_min,
            ToplamSure_Min as total_minutes,
            ForkliftOperator,
            DataEntryOperator
        FROM VW_DollyProcessTimeline WITH (NOLOCK)
        WHERE IslemTarihi BETWEEN :start_date AND :end_date
        {shift_filter}
        ORDER BY TerminalOkutmaZamani DESC
    """)

    results = db.execute(query, {"start_date": start_date, "end_date": end_date, "limit": limit}).fetchall()
    
    return [
        DollyDetailRow(
            dolly_no=row.dolly_no,
            vin_no=row.vin_no,
            part_number=row.part_number,
            group_name=row.group_name,
            eol_name=row.eol_name,
            sefer_numarasi=row.sefer_numarasi,
            plaka_no=row.plaka_no,
            eol_date=row.eol_date,
            scan_time=row.eol_date,
            loading_completed=row.terminal_time,
            terminal_time=row.terminal_time,
            wait_before_scan_min=row.wait_before_scan_min,
            loading_duration_min=row.loading_duration_min,
            terminal_duration_min=row.terminal_duration_min,
            total_minutes=row.total_minutes
        )
        for row in results
    ]

