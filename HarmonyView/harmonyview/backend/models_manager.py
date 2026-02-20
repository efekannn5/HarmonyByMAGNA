"""
Pydantic models for Manager Dashboard API
Analytical data models with date filtering support
"""
from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional

# ==================== REQUEST MODELS ====================
class DateRangeFilter(BaseModel):
    """Date range filter for analytics"""
    start_date: date
    end_date: date
    shift: Optional[int] = None  # 1: 08:00-16:00, 2: 16:00-00:00, 3: 00:00-08:00

# ==================== PROCESS DURATION MODELS ====================
class ProcessDuration(BaseModel):
    """Process duration breakdown per stage"""
    stage_name: str
    avg_duration_minutes: float
    min_duration_minutes: float
    max_duration_minutes: float
    dolly_count: int


class ProcessDurationItem(BaseModel):
    """Per-dolly duration detail for list view"""
    dolly_no: str
    part_number: Optional[str]
    sefer_numarasi: Optional[str]
    plaka_no: Optional[str]
    wait_before_scan_minutes: Optional[int]
    loading_duration_minutes: Optional[int]
    shipment_prep_minutes: Optional[int]
    total_minutes: Optional[int]


class ProcessDurationAnalysis(BaseModel):
    """Complete process duration analysis"""
    production_duration: ProcessDuration  # Uretim (dolly cikartma)
    wait_before_scan_duration: ProcessDuration  # Okutulmadan bekleme
    scanning_duration: ProcessDuration  # Okutulma suresi
    wait_after_scan_duration: ProcessDuration  # ASN/Irsaliye bekleme
    total_process_duration: ProcessDuration  # Toplam surec
    items: List[ProcessDurationItem] = []

# ==================== HEATMAP MODELS ====================
class HourlyHeatmap(BaseModel):
    """Hourly activity heatmap single cell"""
    hour_of_day: int  # 0-23
    day_of_week: int  # 0-6
    dolly_count: int

# ==================== PERFORMANCE METRICS ====================
class DailyPerformance(BaseModel):
    """Daily aggregated performance"""
    date: date
    dolly_count: int
    total_quantity: int
    sefer_count: int
    asn_completion_rate: float
    irsaliye_completion_rate: float

# ==================== EOL ANALYSIS ====================
class EOLPerformance(BaseModel):
    """EOL station performance"""
    eol_name: str
    dolly_count: int
    total_quantity: int
    avg_quantity_per_dolly: float
    sefer_count: int
    asn_completion_rate: float

# ==================== PART ANALYSIS ====================
class PartAnalysisItem(BaseModel):
    """Part-based time analysis"""
    part_number: str
    group_name: Optional[str] = None
    dolly_count: int
    total_quantity: int
    avg_wait_before_scan: float  # EOL -> Okutma (dakika)
    avg_loading_duration: float  # Okutma -> Yükleme (dakika)
    avg_terminal_duration: float # Yükleme -> Sevkiyat (dakika)
    avg_total_duration: float    # Toplam süre (dakika)
    min_total_duration: float
    max_total_duration: float

# ==================== GROUP ANALYSIS ====================
class GroupAnalysisItem(BaseModel):
    """DollyGroup-based analysis"""
    group_id: int
    group_name: str
    part_count: int
    dolly_count: int
    total_quantity: int
    avg_wait_before_scan: float
    avg_loading_duration: float
    avg_terminal_duration: float
    avg_total_duration: float

# ==================== DETAILED DOLLY LIST ====================
class DollyDetailRow(BaseModel):
    """Detailed dolly row for Excel-like table"""
    dolly_no: str
    vin_no: Optional[str] = None
    part_number: Optional[str] = None
    group_name: Optional[str] = None
    eol_name: Optional[str] = None
    sefer_numarasi: Optional[str] = None
    plaka_no: Optional[str] = None
    eol_date: Optional[datetime] = None
    scan_time: Optional[datetime] = None
    loading_completed: Optional[datetime] = None
    terminal_time: Optional[datetime] = None
    wait_before_scan_min: Optional[float] = None
    loading_duration_min: Optional[float] = None
    terminal_duration_min: Optional[float] = None
    total_minutes: Optional[float] = None

# ==================== DASHBOARD DATA ====================
class ManagerDashboardData(BaseModel):
    """Complete manager dashboard data"""
    date_range: DateRangeFilter
    process_duration_analysis: ProcessDurationAnalysis
    hourly_heatmap: List[HourlyHeatmap]
    daily_performances: List[DailyPerformance]
    eol_performances: List[EOLPerformance]
    part_analysis: List[PartAnalysisItem] = []
    group_analysis: List[GroupAnalysisItem] = []
    dolly_details: List[DollyDetailRow] = []
    summary_stats: dict
