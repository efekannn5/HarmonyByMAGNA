"""
Harmony Control Tower - Optimized SQL Queries
All queries are READ-ONLY and optimized for performance
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Dict, Any
from models import (
    QueueStatus, EOLDistribution, LoadingSession,
    DailyStatistics, RecentActivity, PartNumberSummary
)

# ==================== QUEUE STATUS ====================
def get_queue_status(db: Session) -> QueueStatus:
    """Get current queue status from DollyEOLInfo - DOLLY based not VIN based"""
    query = text("""
        SELECT 
            COUNT(DISTINCT DollyNo) as total_dollies,
            SUM(CAST(Adet AS INT)) as total_parts,
            COUNT(*) as total_vins,
            MIN(EOLDATE) as oldest_dolly_date,
            MAX(EOLDATE) as newest_dolly_date
        FROM DollyEOLInfo WITH (NOLOCK)
    """)
    
    result = db.execute(query).fetchone()
    
    return QueueStatus(
        total_dollies=result.total_dollies or 0,
        total_parts=result.total_parts or 0,
        unique_vins=result.total_vins or 0,
        oldest_dolly_date=result.oldest_dolly_date,
        newest_dolly_date=result.newest_dolly_date
    )

# ==================== EOL DISTRIBUTION ====================
def get_eol_distribution(db: Session) -> List[EOLDistribution]:
    """Get EOL station distribution - DOLLY based not VIN based"""
    query = text("""
        SELECT 
            EOLName as eol_name,
            COUNT(DISTINCT DollyNo) as dolly_count,
            SUM(CAST(Adet AS INT)) as part_count
        FROM DollyEOLInfo WITH (NOLOCK)
        WHERE EOLName IS NOT NULL
        GROUP BY EOLName
        ORDER BY dolly_count DESC
    """)
    
    results = db.execute(query).fetchall()
    
    total = sum(r.dolly_count for r in results)
    
    return [
        EOLDistribution(
            eol_name=r.eol_name,
            dolly_count=r.dolly_count,
            part_count=r.part_count or 0,
            percentage=round((r.dolly_count / total * 100), 2) if total > 0 else 0
        )
        for r in results
    ]

# ==================== LOADING SESSIONS ====================
def get_loading_sessions(db: Session) -> List[LoadingSession]:
    """Get active loading sessions from DollySubmissionHold"""
    query = text("""
        SELECT 
            LoadingSessionId as session_id,
            MAX(TerminalUser) as operator_name,
            COUNT(*) as dolly_count,
            MAX(ScanOrder) as scan_order_max,
            MAX(Status) as status,
            MAX(LoadingCompletedAt) as loading_completed_at,
            MIN(CreatedAt) as created_at
        FROM DollySubmissionHold WITH (NOLOCK)
        WHERE Status IN ('scanned', 'loading_completed', 'pending')
        GROUP BY LoadingSessionId
        ORDER BY created_at DESC
    """)
    
    results = db.execute(query).fetchall()
    
    return [
        LoadingSession(
            session_id=r.session_id or "N/A",
            operator_name=r.operator_name or "Unknown",
            dolly_count=r.dolly_count,
            scan_order_max=r.scan_order_max or 0,
            status=r.status or "unknown",
            loading_completed_at=r.loading_completed_at,
            created_at=r.created_at or datetime.now()
        )
        for r in results
    ]

# ==================== DAILY STATISTICS ====================
def get_daily_statistics(db: Session) -> DailyStatistics:
    """Get today's statistics from SeferDollyEOL"""
    today = date.today()
    
    query = text("""
        SELECT 
            COUNT(*) as total_shipped,
            SUM(CAST(Adet AS INT)) as total_parts,
            COUNT(DISTINCT SeferNumarasi) as unique_sefers,
            SUM(CASE WHEN ASNDate IS NOT NULL THEN 1 ELSE 0 END) as asn_count,
            SUM(CASE WHEN IrsaliyeDate IS NOT NULL THEN 1 ELSE 0 END) as irsaliye_count
        FROM SeferDollyEOL WITH (NOLOCK)
        WHERE CAST(TerminalDate AS DATE) = :today
    """)
    
    result = db.execute(query, {"today": today}).fetchone()
    
    avg_dollies = (result.total_shipped / result.unique_sefers) if result.unique_sefers > 0 else 0
    
    return DailyStatistics(
        total_shipped=result.total_shipped or 0,
        total_parts=result.total_parts or 0,
        unique_sefers=result.unique_sefers or 0,
        asn_count=result.asn_count or 0,
        irsaliye_count=result.irsaliye_count or 0,
        avg_dollies_per_sefer=round(avg_dollies, 2)
    )

# ==================== RECENT ACTIVITIES ====================
def get_recent_activities(db: Session, limit: int = 10) -> List[RecentActivity]:
    """Get recent activities from DollyLifecycle"""
    query = text("""
        SELECT TOP (:limit)
            Status as activity_type,
            DollyNo as dolly_no,
            VinNo as vin_no,
            Metadata as metadata,
            CreatedAt as timestamp
        FROM DollyLifecycle WITH (NOLOCK)
        WHERE Status IN ('EOL_READY', 'SCAN_CAPTURED', 'COMPLETED_ASN', 'COMPLETED_IRSALIYE')
        ORDER BY CreatedAt DESC
    """)
    
    results = db.execute(query, {"limit": limit}).fetchall()
    
    activities = []
    for r in results:
        # Parse metadata if available (stored as JSON string)
        import json
        metadata = {}
        if r.metadata:
            try:
                metadata = json.loads(r.metadata)
            except:
                pass
        
        activities.append(RecentActivity(
            activity_type=r.activity_type,
            dolly_no=r.dolly_no,
            vin_no=r.vin_no,
            operator=metadata.get("operator"),
            timestamp=r.timestamp,
            eol_name=metadata.get("eol_name"),
            sefer_numarasi=metadata.get("sefer_numarasi")
        ))
    
    return activities

# ==================== PART NUMBER SUMMARY ====================
def get_part_summaries(db: Session, limit: int = 5) -> List[PartNumberSummary]:
    """Get part number summaries - PartNumber only exists in DollySubmissionHold and SeferDollyEOL"""
    query = text("""
        WITH PartStats AS (
            SELECT 
                PartNumber,
                COUNT(*) as dolly_count,
                'loading' as status,
                NULL as last_shipped
            FROM DollySubmissionHold WITH (NOLOCK)
            WHERE PartNumber IS NOT NULL
            GROUP BY PartNumber
            
            UNION ALL
            
            SELECT 
                PartNumber,
                COUNT(*) as dolly_count,
                'shipped' as status,
                MAX(ASNDate) as last_shipped
            FROM SeferDollyEOL WITH (NOLOCK)
            WHERE PartNumber IS NOT NULL
                AND CAST(TerminalDate AS DATE) = CAST(GETDATE() AS DATE)
            GROUP BY PartNumber
        )
        SELECT TOP (:limit)
            PartNumber as part_number,
            SUM(dolly_count) as dolly_count,
            MAX(last_shipped) as last_shipped,
            MAX(status) as status
        FROM PartStats
        GROUP BY PartNumber
        ORDER BY dolly_count DESC
    """)
    
    results = db.execute(query, {"limit": limit}).fetchall()
    
    return [
        PartNumberSummary(
            part_number=r.part_number,
            dolly_count=r.dolly_count,
            last_shipped=r.last_shipped,
            status=r.status
        )
        for r in results
    ]

# ==================== DOLLY FILLING STATUS (PER EOL) ====================
def get_active_dolly_filling(db: Session) -> List[Dict[str, Any]]:
    """Get current dolly filling status for each EOL line"""
    query = text("""
        WITH LatestDolliesPerEOL AS (
            SELECT 
                EOLName,
                DollyNo,
                COUNT(DISTINCT VinNo) as current_vin_count,
                MAX(InsertedAt) as last_update,
                ROW_NUMBER() OVER (PARTITION BY EOLName ORDER BY MAX(InsertedAt) DESC) as rn
            FROM DollyEOLInfo WITH (NOLOCK)
            WHERE EOLName IS NOT NULL
            GROUP BY EOLName, DollyNo
        ),
        EOLAverages AS (
            SELECT 
                EOLName,
                AVG(CAST(vin_count AS FLOAT)) as avg_vins_per_dolly
            FROM (
                SELECT EOLName, DollyNo, COUNT(DISTINCT VinNo) as vin_count
                FROM DollyEOLInfoBackup WITH (NOLOCK)
                WHERE CAST(EOLDATE AS DATE) = CAST(GETDATE() AS DATE)
                    AND EOLName IS NOT NULL
                GROUP BY EOLName, DollyNo
            ) AS DollyCounts
            GROUP BY EOLName
        )
        SELECT 
            l.EOLName,
            l.DollyNo as active_dolly,
            l.current_vin_count,
            l.last_update,
            ISNULL(a.avg_vins_per_dolly, 10) as avg_capacity
        FROM LatestDolliesPerEOL l
        LEFT JOIN EOLAverages a ON l.EOLName = a.EOLName
        WHERE l.rn = 1
        ORDER BY l.last_update DESC
    """)
    
    results = db.execute(query).fetchall()
    
    dolly_filling_list = []
    for r in results:
        avg_capacity = r.avg_capacity or 10
        remaining = max(0, int(avg_capacity - r.current_vin_count))
        fill_percentage = min(100, int((r.current_vin_count / avg_capacity) * 100))
        
        dolly_filling_list.append({
            "eol_name": r.EOLName,
            "active_dolly": r.active_dolly,
            "current_vins": r.current_vin_count,
            "estimated_capacity": int(avg_capacity),
            "fill_percentage": fill_percentage,
            "remaining_vins": remaining,
            "last_update": r.last_update.isoformat() if r.last_update else None
        })
    
    return dolly_filling_list

# ==================== LINE VISUALIZATION (TV DASHBOARD - CUSTOM DESIGN) ====================
def get_line_details(db: Session) -> Dict[str, Any]:
    """Get detailed visualization data for ALL EOL lines (Active, Ready, Scanned)"""
    
    # 1. Get Active Filling Status (Same as before)
    active_query = text("""
        WITH LatestDollies AS (
            SELECT 
                EOLName,
                DollyNo,
                MAX(DollyOrderNo) as DollyOrderNo,
                COUNT(DISTINCT VinNo) as current_vins,
                MAX(InsertedAt) as last_update,
                ROW_NUMBER() OVER (PARTITION BY EOLName ORDER BY MAX(InsertedAt) DESC) as rn
            FROM DollyEOLInfo WITH (NOLOCK)
            WHERE EOLName IS NOT NULL
            GROUP BY EOLName, DollyNo
        ),
        EOLAverages AS (
            SELECT 
                EOLName,
                AVG(CAST(vin_count AS FLOAT)) as avg_vins_per_dolly
            FROM (
                SELECT EOLName, DollyNo, COUNT(DISTINCT VinNo) as vin_count
                FROM DollyEOLInfoBackup WITH (NOLOCK)
                WHERE EOLName IS NOT NULL
                GROUP BY EOLName, DollyNo
            ) AS DollyCounts
            GROUP BY EOLName
        )
        SELECT 
            l.EOLName, 
            l.DollyNo, 
            l.DollyOrderNo,
            l.current_vins,
            l.last_update,
            ISNULL(a.avg_vins_per_dolly, 12) as avg_capacity
        FROM LatestDollies l
        LEFT JOIN EOLAverages a ON l.EOLName = a.EOLName
        WHERE l.rn = 1
    """)
    
    active_results = db.execute(active_query).fetchall()
    
    # 2. Get SCANNED Queue (From DollySubmissionHold)
    # Group by DollyNo + EOLName to deduplicate at query level (same dolly may have multiple rows for different parts)
    scanned_query = text("""
        SELECT 
            EOLName,
            DollyNo,
            MAX(DollyOrderNo) as DollyOrderNo,
            MAX(COALESCE(SubmittedAt, CreatedAt)) as sort_date,
            MAX(Status) as status,
            0 as duration
        FROM DollySubmissionHold WITH (NOLOCK)
        WHERE CreatedAt > DATEADD(HOUR, -24, GETDATE())
        GROUP BY EOLName, DollyNo
        ORDER BY sort_date DESC
    """)
    
    scanned_results = db.execute(scanned_query).fetchall()
    
    # 3. Get READY Queue (Completed in EOL but NOT in SubmissionHold)
    ready_query = text("""
        WITH DollyTimeline AS (
            SELECT 
                d.EOLName,
                d.DollyNo,
                MAX(d.DollyOrderNo) as DollyOrderNo,
                MAX(d.InsertedAt) as dolly_completed_at,
                DATEDIFF(MINUTE, MIN(d.InsertedAt), MAX(d.InsertedAt)) as duration_minutes
            FROM DollyEOLInfo d WITH (NOLOCK)
            WHERE d.EOLName IS NOT NULL
            GROUP BY d.EOLName, d.DollyNo
        ),
        SubmittedDollies AS (
            SELECT DollyNo FROM DollySubmissionHold WITH (NOLOCK)
        )
        SELECT
            dt.EOLName,
            dt.DollyNo,
            dt.DollyOrderNo,
            dt.dolly_completed_at,
            dt.duration_minutes
        FROM DollyTimeline dt
        LEFT JOIN SubmittedDollies sd ON dt.DollyNo = sd.DollyNo
        WHERE sd.DollyNo IS NULL 
          AND dt.dolly_completed_at > DATEADD(HOUR, -24, GETDATE())
        ORDER BY dt.dolly_completed_at DESC
    """)
    
    ready_results = db.execute(ready_query).fetchall()
    
    # Process results
    lines = {}
    
    # Initialize lines from active results first
    for r in active_results:
        capacity = max(1, int(round(r.avg_capacity)))
        lines[r.EOLName] = {
            "active": {
                "dolly_no": r.DollyNo,
                "dolly_order_no": r.DollyOrderNo,
                "current_vins": r.current_vins,
                "capacity": capacity,
                "fill_percentage": min(100, int((r.current_vins / capacity) * 100))
            },
            "queue": [],   # Ready
            "scanned": []  # Scanned/Green
        }
        
    # Process Ready Queue
    seen_ready_dollies = set()
    for r in ready_results:
        if r.EOLName not in lines:
            continue
        
        # Don't show active dolly in queue
        if lines[r.EOLName]["active"] and lines[r.EOLName]["active"]["dolly_no"] == r.DollyNo:
            continue
            
        # Create a unique identifier for deduplication
        unique_key = f"{r.EOLName}_{r.DollyNo}"
        
        if unique_key in seen_ready_dollies:
            continue

        if len(lines[r.EOLName]["queue"]) < 8: # Limit visual noise
            lines[r.EOLName]["queue"].append({
                "dolly_no": r.DollyNo,
                "dolly_order_no": r.DollyOrderNo,
                "completed_at": r.dolly_completed_at.isoformat(),
                "duration": r.duration_minutes
            })
            seen_ready_dollies.add(unique_key)
            
    # Process Scanned Queue
    seen_dollies = set()
    for r in scanned_results:
        if r.EOLName and r.EOLName in lines:
            # Create a unique identifier for deduplication
            unique_key = f"{r.EOLName}_{r.DollyNo}"
            
            if unique_key in seen_dollies:
                continue
                
            if len(lines[r.EOLName]["scanned"]) < 8:
                lines[r.EOLName]["scanned"].append({
                    "dolly_no": r.DollyNo,
                    "dolly_order_no": r.DollyOrderNo,
                    "completed_at": r.sort_date.isoformat(),
                    "status": r.status,
                    "duration": r.duration
                })
                seen_dollies.add(unique_key)
            
    return lines

# ==================== SHIFT-BASED STATISTICS ====================
def get_shift_statistics(db: Session) -> Dict[str, Any]:
    """Get statistics by shift (08:00-16:00, 16:00-00:00, 00:00-08:00)"""
    
    # Determine current shift
    from datetime import datetime
    now = datetime.now()
    current_hour = now.hour
    
    if 8 <= current_hour < 16:
        current_shift = "Shift_1"  # 08:00-16:00
        shift_start = f"{now.strftime('%Y-%m-%d')} 08:00:00"
        shift_end = f"{now.strftime('%Y-%m-%d')} 16:00:00"
        prev_shift_start = f"{now.strftime('%Y-%m-%d')} 00:00:00"
        prev_shift_end = f"{now.strftime('%Y-%m-%d')} 08:00:00"
    elif 16 <= current_hour < 24:
        current_shift = "Shift_2"  # 16:00-00:00
        shift_start = f"{now.strftime('%Y-%m-%d')} 16:00:00"
        shift_end = f"{now.strftime('%Y-%m-%d')} 23:59:59"
        prev_shift_start = f"{now.strftime('%Y-%m-%d')} 08:00:00"
        prev_shift_end = f"{now.strftime('%Y-%m-%d')} 16:00:00"
    else:  # 00:00-08:00
        current_shift = "Shift_3"
        shift_start = f"{now.strftime('%Y-%m-%d')} 00:00:00"
        shift_end = f"{now.strftime('%Y-%m-%d')} 08:00:00"
        from datetime import timedelta
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        prev_shift_start = f"{yesterday} 16:00:00"
        prev_shift_end = f"{yesterday} 23:59:59"
    
    # Current shift stats
    query_current = text("""
        SELECT 
            COUNT(DISTINCT DollyNo) as dolly_count,
            COUNT(DISTINCT PartNumber) as part_count,
            COUNT(DISTINCT SeferNumarasi) as sefer_count
        FROM SeferDollyEOL WITH (NOLOCK)
        WHERE TerminalDate >= :shift_start
            AND TerminalDate < :shift_end
    """)
    
    current = db.execute(query_current, {
        "shift_start": shift_start,
        "shift_end": shift_end
    }).fetchone()
    
    # Previous shift stats
    query_prev = text("""
        SELECT 
            COUNT(DISTINCT DollyNo) as dolly_count,
            COUNT(DISTINCT PartNumber) as part_count,
            COUNT(DISTINCT SeferNumarasi) as sefer_count
        FROM SeferDollyEOL WITH (NOLOCK)
        WHERE TerminalDate >= :shift_start
            AND TerminalDate < :shift_end
    """)
    
    previous = db.execute(query_prev, {
        "shift_start": prev_shift_start,
        "shift_end": prev_shift_end
    }).fetchone()
    
    return {
        "current_shift": {
            "name": current_shift,
            "start_time": shift_start.split()[1],
            "end_time": shift_end.split()[1],
            "dolly_count": current.dolly_count or 0,
            "part_count": current.part_count or 0,
            "sefer_count": current.sefer_count or 0
        },
        "previous_shift": {
            "dolly_count": previous.dolly_count or 0,
            "part_count": previous.part_count or 0,
            "sefer_count": previous.sefer_count or 0
        }
    }

# ==================== GROUP-BASED SUMMARY (DOLLY GROUPS) ====================
def get_part_based_summary(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Get group-based summary - Use DollyGroup names instead of PartNumber"""
    query = text("""
        WITH GroupMapping AS (
            SELECT 
                dge.GroupId,
                dg.GroupName,
                dge.PWorkStationId,
                dge.ShippingTag,
                pw.PWorkStationName as EOLName
            FROM DollyGroupEOL dge WITH (NOLOCK)
            INNER JOIN DollyGroup dg WITH (NOLOCK) ON dge.GroupId = dg.Id
            INNER JOIN PWorkStation pw WITH (NOLOCK) ON dge.PWorkStationId = pw.Id
            WHERE dg.IsActive = 1
        )
        SELECT TOP (:limit)
            gm.GroupName,
            gm.ShippingTag,
            COUNT(DISTINCT s.DollyNo) as dolly_count,
            COUNT(DISTINCT s.VinNo) as vin_count,
            COUNT(DISTINCT s.SeferNumarasi) as sefer_count,
            MAX(s.ASNDate) as last_shipment
        FROM SeferDollyEOL s WITH (NOLOCK)
        INNER JOIN GroupMapping gm ON s.EOLName = gm.EOLName
        WHERE CAST(s.TerminalDate AS DATE) = CAST(GETDATE() AS DATE)
        GROUP BY gm.GroupName, gm.ShippingTag
        ORDER BY dolly_count DESC
    """)
    
    results = db.execute(query, {"limit": limit}).fetchall()
    
    return [
        {
            "group_name": r.GroupName,
            "shipping_tag": r.ShippingTag,
            "dolly_count": r.dolly_count,
            "vin_count": r.vin_count,
            "sefer_count": r.sefer_count,
            "last_shipment": r.last_shipment.isoformat() if r.last_shipment else None
        }
        for r in results
    ]

# ==================== PROCESS TIMELINE ====================
def get_process_timeline(db: Session, limit: int = 20) -> List[Dict[str, Any]]:
    """Get process timeline from DollyLifecycle"""
    query = text("""
        WITH LatestActivities AS (
            SELECT 
                DollyNo,
                VinNo,
                Status,
                CreatedAt,
                ROW_NUMBER() OVER (PARTITION BY DollyNo, VinNo ORDER BY CreatedAt DESC) as rn
            FROM DollyLifecycle WITH (NOLOCK)
        )
        SELECT TOP (:limit)
            DollyNo,
            VinNo,
            Status,
            CreatedAt
        FROM LatestActivities
        WHERE rn = 1
        ORDER BY CreatedAt DESC
    """)
    
    results = db.execute(query, {"limit": limit}).fetchall()
    
    return [
        {
            "dolly_no": r.DollyNo,
            "vin_no": r.VinNo,
            "status": r.Status,
            "created_at": r.CreatedAt.isoformat() if r.CreatedAt else None
        }
        for r in results
    ]

# ==================== PERFORMANCE METRICS ====================
def get_performance_metrics(db: Session) -> Dict[str, Any]:
    """Get performance metrics - Focus on DOLLY counts not VINs"""
    # Today's total dollies shipped
    query_dollies = text("""
        SELECT 
            COUNT(DISTINCT DollyNo) as total_dollies_shipped
        FROM SeferDollyEOL WITH (NOLOCK)
        WHERE CAST(TerminalDate AS DATE) = CAST(GETDATE() AS DATE)
    """)
    
    result_dollies = db.execute(query_dollies).fetchone()
    
    # Average processing time per dolly (EOL to Shipped) - Fixed with CTE
    query_time = text("""
        WITH DollyTimes AS (
            SELECT 
                DollyNo,
                DATEDIFF(MINUTE, MIN(EOLDate), MAX(TerminalDate)) as processing_minutes
            FROM SeferDollyEOL WITH (NOLOCK)
            WHERE CAST(TerminalDate AS DATE) = CAST(GETDATE() AS DATE)
                AND EOLDate IS NOT NULL
                AND TerminalDate IS NOT NULL
            GROUP BY DollyNo
        )
        SELECT AVG(CAST(processing_minutes AS FLOAT)) as avg_processing_minutes
        FROM DollyTimes
    """)
    
    result_time = db.execute(query_time).fetchone()
    
    # Dollies per hour
    query_hourly = text("""
        SELECT 
            COUNT(DISTINCT DollyNo) as dollies_this_hour
        FROM SeferDollyEOL WITH (NOLOCK)
        WHERE TerminalDate >= DATEADD(HOUR, -1, GETDATE())
    """)
    
    result_hourly = db.execute(query_hourly).fetchone()
    
    return {
        "total_dollies_shipped": result_dollies.total_dollies_shipped or 0,
        "avg_processing_minutes": round(result_time.avg_processing_minutes or 0, 1),
        "dollies_per_hour": result_hourly.dollies_this_hour or 0
    }

# ==================== GET ALL DASHBOARD DATA ====================
def get_dashboard_data(db: Session) -> Dict[str, Any]:
    """Get all dashboard data in one call"""
    return {
        "queue_status": get_queue_status(db),
        "eol_distribution": get_eol_distribution(db),
        "loading_sessions": get_loading_sessions(db),
        "daily_statistics": get_daily_statistics(db),
        "recent_activities": get_recent_activities(db, limit=15),
        "part_summaries": get_part_summaries(db, limit=8),
        "process_timeline": get_process_timeline(db, limit=20),
        "performance_metrics": get_performance_metrics(db),
        "active_dolly_filling": get_active_dolly_filling(db),
        "shift_statistics": get_shift_statistics(db),
        "part_based_summary": get_part_based_summary(db, limit=10),
        "line_visualization": get_line_details(db),
        "last_updated": datetime.now()
    }
