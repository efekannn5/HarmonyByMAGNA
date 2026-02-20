"""
Harmony Control Tower - Pydantic Models
Data models for API responses
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict

class LineDetails(BaseModel):
    """Details for a specific EOL line (Active + Queue)"""
    active: Optional[dict] = Field(None, description="Currently filling dolly")
    queue: List[dict] = Field(default=[], description="Completed dollies waiting for submission")
    scanned: List[dict] = Field(default=[], description="Submitted/Scanned dollies (Green)")

class QueueStatus(BaseModel):
    """Current queue status from DollyEOLInfo"""
    total_dollies: int = Field(..., description="Total dollies in queue")
    total_parts: int = Field(..., description="Total parts count")
    unique_vins: int = Field(..., description="Unique VIN count")
    oldest_dolly_date: Optional[datetime] = Field(None, description="Oldest dolly in queue")
    newest_dolly_date: Optional[datetime] = Field(None, description="Newest dolly in queue")

class EOLDistribution(BaseModel):
    """EOL station distribution"""
    eol_name: str
    dolly_count: int
    part_count: int
    percentage: float

class LoadingSession(BaseModel):
    """Loading session from DollySubmissionHold"""
    session_id: str
    operator_name: str
    dolly_count: int
    scan_order_max: int
    status: str
    loading_completed_at: Optional[datetime]
    created_at: datetime

class DailyStatistics(BaseModel):
    """Daily statistics from SeferDollyEOL"""
    total_shipped: int
    total_parts: int
    unique_sefers: int
    asn_count: int
    irsaliye_count: int
    avg_dollies_per_sefer: float

class RecentActivity(BaseModel):
    """Recent activity feed"""
    activity_type: str  # "eol_ready", "scanned", "shipped"
    dolly_no: str
    vin_no: str
    operator: Optional[str]
    timestamp: datetime
    eol_name: Optional[str]
    sefer_numarasi: Optional[str]

class PartNumberSummary(BaseModel):
    """Part number summary"""
    part_number: str
    dolly_count: int
    last_shipped: Optional[datetime]
    status: str  # "in_queue", "loading", "shipped"

class DashboardData(BaseModel):
    """Complete dashboard data"""
    line_visualization: Optional[Dict[str, LineDetails]] = Field(None, description="Visual details for V710/J74 lines")
    queue_status: QueueStatus
    eol_distribution: List[EOLDistribution]
    loading_sessions: List[LoadingSession]
    daily_statistics: DailyStatistics
    recent_activities: List[RecentActivity]
    part_summaries: List[PartNumberSummary]
    last_updated: datetime
