"""
Analytics API Routes
====================
RESTful API endpoints for analytics data.
All endpoints are READ-ONLY.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required
from sqlalchemy import text

from app.extensions import db


analytics_api_bp = Blueprint("analytics_api", __name__)


def _execute_view_query(view_name: str, filters: Dict[str, Any] = None) -> List[Dict]:
    """
    Execute query on analytics view with optional filters.
    
    Args:
        view_name: Name of the analytics view
        filters: Optional dictionary of filters
    
    Returns:
        List of result dictionaries
    """
    query = f"SELECT * FROM {view_name}"
    where_clauses = []
    params = {}
    
    if filters:
        if "date_from" in filters:
            where_clauses.append("ProductionDate >= :date_from")
            params["date_from"] = filters["date_from"]
        
        if "date_to" in filters:
            where_clauses.append("ProductionDate <= :date_to")
            params["date_to"] = filters["date_to"]
        
        if "production_line" in filters and filters["production_line"]:
            where_clauses.append("ProductionLine = :production_line")
            params["production_line"] = filters["production_line"]
        
        if "part_number" in filters and filters["part_number"]:
            where_clauses.append("PartNumber = :part_number")
            params["part_number"] = filters["part_number"]
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    result = db.session.execute(text(query), params)
    columns = result.keys()
    
    return [dict(zip(columns, row)) for row in result.fetchall()]


def _serialize_datetime(obj):
    """Convert datetime objects to ISO format string."""
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    return obj


@analytics_api_bp.route("/overview")
@login_required
def get_overview():
    """
    Get high-level overview statistics.
    
    Returns:
        JSON with current KPIs and status
    """
    try:
        # Get date range from query params (default: today)
        date_from = request.args.get("date_from", datetime.now().date().isoformat())
        date_to = request.args.get("date_to", datetime.now().date().isoformat())
        
        # Real-time status
        realtime_query = """
            SELECT 
                CurrentStage,
                DollyCount,
                AvgWaitHours,
                MaxWaitHours,
                CriticalAlerts,
                WarningAlerts
            FROM vw_Analytics_RealtimeStatus
        """
        realtime_result = db.session.execute(text(realtime_query))
        realtime_data = {row[0]: dict(zip(realtime_result.keys(), row)) for row in realtime_result.fetchall()}
        
        # Daily summary
        daily_query = text("""
            SELECT TOP 1
                TotalDollys,
                CompletedDollys,
                ScanningDollys,
                LoadingCompletedDollys,
                WebProcessingDollys,
                ProductionDollys,
                AvgHours_Total,
                TargetAchievementPercent
            FROM vw_Analytics_DailySummary
            WHERE ProductionDate = :date
            ORDER BY ProductionDate DESC
        """)
        daily_result = db.session.execute(daily_query, {"date": date_to}).fetchone()
        
        if daily_result:
            daily_data = dict(zip(
                ["TotalDollys", "CompletedDollys", "ScanningDollys", "LoadingCompletedDollys", 
                 "WebProcessingDollys", "ProductionDollys", "AvgHours_Total", "TargetAchievementPercent"],
                daily_result
            ))
        else:
            daily_data = {
                "TotalDollys": 0,
                "CompletedDollys": 0,
                "ScanningDollys": 0,
                "LoadingCompletedDollys": 0,
                "WebProcessingDollys": 0,
                "ProductionDollys": 0,
                "AvgHours_Total": 0,
                "TargetAchievementPercent": 0
            }
        
        return jsonify({
            "success": True,
            "data": {
                "realtime": realtime_data,
                "daily": daily_data,
                "date_range": {
                    "from": date_from,
                    "to": date_to
                }
            }
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in overview API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analytics_api_bp.route("/timeline")
@login_required
def get_timeline():
    """
    Get timeline data for trend charts.
    
    Query params:
        - date_from: Start date (default: 7 days ago)
        - date_to: End date (default: today)
        - granularity: 'hourly' or 'daily' (default: daily)
    
    Returns:
        JSON with timeline data
    """
    try:
        date_to = request.args.get("date_to", datetime.now().date().isoformat())
        date_from = request.args.get("date_from", (datetime.now().date() - timedelta(days=7)).isoformat())
        granularity = request.args.get("granularity", "daily")
        
        if granularity == "hourly":
            query = text("""
                SELECT 
                    ProductionDate,
                    ProductionHour,
                    ProductionShift,
                    DollysProduced,
                    DollysCompleted,
                    AvgHours_Total,
                    OnTimePercent
                FROM vw_Analytics_HourlyThroughput
                WHERE ProductionDate BETWEEN :date_from AND :date_to
                ORDER BY ProductionDate, ProductionHour
            """)
        else:
            query = text("""
                SELECT 
                    ProductionDate,
                    TotalDollys,
                    CompletedDollys,
                    AvgHours_Production_To_Scan,
                    AvgHours_Scan_To_Loading,
                    AvgHours_Loading_To_WebEntry,
                    AvgHours_WebEntry_To_Shipment,
                    AvgHours_Total,
                    TargetAchievementPercent
                FROM vw_Analytics_DailySummary
                WHERE ProductionDate BETWEEN :date_from AND :date_to
                ORDER BY ProductionDate
            """)
        
        result = db.session.execute(query, {"date_from": date_from, "date_to": date_to})
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result.fetchall()]
        
        # Convert datetime objects
        for item in data:
            for key, value in item.items():
                item[key] = _serialize_datetime(value)
        
        return jsonify({
            "success": True,
            "data": data,
            "meta": {
                "granularity": granularity,
                "date_from": date_from,
                "date_to": date_to,
                "count": len(data)
            }
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in timeline API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analytics_api_bp.route("/line-process-metrics")
@login_required
def get_line_process_metrics():
    """
    Get per-line process metrics across the end-to-end journey.
    
    Returns:
        JSON list with counts and average durations (in minutes) per production line.
    """
    try:
        query = text("""
            SELECT
                ProductionLine,
                COUNT(*) AS total_dollies,
                SUM(CASE WHEN CurrentStage = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_dollies,
                SUM(CAST(ISNULL(Quantity, 0) AS INT)) AS total_quantity,
                AVG(CAST(Duration_Production_To_Scan AS FLOAT)) AS avg_prod_to_scan_min,
                AVG(CAST(Duration_Scan_To_Loading AS FLOAT)) AS avg_scan_to_loading_min,
                AVG(CAST(Duration_Loading_To_WebEntry AS FLOAT)) AS avg_loading_to_web_min,
                AVG(CAST(Duration_WebEntry_To_Shipment AS FLOAT)) AS avg_web_to_ship_min,
                AVG(CAST(Duration_Total AS FLOAT)) AS avg_total_min,
                MAX(ProductionCompletedAt) AS last_activity
            FROM vw_Analytics_DollyJourney
            GROUP BY ProductionLine
            ORDER BY ProductionLine
        """)
        
        rows = db.session.execute(query).fetchall()
        columns = [
            "production_line",
            "total_dollies",
            "completed_dollies",
            "total_quantity",
            "avg_prod_to_scan_min",
            "avg_scan_to_loading_min",
            "avg_loading_to_web_min",
            "avg_web_to_ship_min",
            "avg_total_min",
            "last_activity",
        ]
        
        data = []
        for row in rows:
            entry = dict(zip(columns, row))
            if entry["last_activity"] and isinstance(entry["last_activity"], datetime):
                entry["last_activity"] = entry["last_activity"].isoformat()
            data.append(entry)
        
        return jsonify({"success": True, "data": data})
    except Exception as e:
        current_app.logger.error(f"Error in line-process-metrics API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_api_bp.route("/line-performance")
@login_required
def get_line_performance():
    """
    Get performance data by production line.
    
    Query params:
        - date_from: Start date
        - date_to: End date
    
    Returns:
        JSON with line performance data
    """
    try:
        date_to = request.args.get("date_to", datetime.now().date().isoformat())
        date_from = request.args.get("date_from", (datetime.now().date() - timedelta(days=7)).isoformat())
        
        query = text("""
            SELECT 
                ProductionLine,
                SUM(TotalDollys) AS TotalDollys,
                SUM(CompletedDollys) AS CompletedDollys,
                AVG(AvgHours_Total) AS AvgHours_Total,
                AVG(PerformanceScore) AS PerformanceScore
            FROM vw_Analytics_LinePerformance
            WHERE ProductionDate BETWEEN :date_from AND :date_to
            GROUP BY ProductionLine
            ORDER BY AvgHours_Total ASC
        """)
        
        result = db.session.execute(query, {"date_from": date_from, "date_to": date_to})
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result.fetchall()]
        
        return jsonify({
            "success": True,
            "data": data,
            "meta": {
                "date_from": date_from,
                "date_to": date_to
            }
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in line performance API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analytics_api_bp.route("/bottlenecks")
@login_required
def get_bottlenecks():
    """
    Get current bottlenecks and delayed dollys.
    
    Query params:
        - alert_level: Filter by alert level (CRITICAL, WARNING, ATTENTION)
        - limit: Max results (default: 50)
    
    Returns:
        JSON with bottleneck data
    """
    try:
        alert_level = request.args.get("alert_level", None)
        limit = int(request.args.get("limit", 50))
        
        query_str = """
            SELECT TOP :limit
                DollyNo,
                VinNo,
                PartNumber,
                ProductionLine,
                CurrentStage,
                ProductionCompletedAt,
                Hours_Total,
                AlertLevel,
                BottleneckStage,
                CurrentWaitHours
            FROM vw_Analytics_Bottlenecks
        """
        
        params = {"limit": limit}
        
        if alert_level:
            query_str += " WHERE AlertLevel = :alert_level"
            params["alert_level"] = alert_level
        
        query_str += " ORDER BY Hours_Total DESC"
        
        result = db.session.execute(text(query_str), params)
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result.fetchall()]
        
        # Convert datetime objects
        for item in data:
            for key, value in item.items():
                item[key] = _serialize_datetime(value)
        
        return jsonify({
            "success": True,
            "data": data,
            "meta": {
                "count": len(data),
                "alert_level": alert_level
            }
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in bottlenecks API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analytics_api_bp.route("/operator-performance")
@login_required
def get_operator_performance():
    """
    Get operator performance statistics (anonymized).
    
    Returns:
        JSON with operator performance data
    """
    try:
        date_to = request.args.get("date_to", datetime.now().date().isoformat())
        date_from = request.args.get("date_from", (datetime.now().date() - timedelta(days=7)).isoformat())
        
        query = text("""
            SELECT 
                OperatorID_Forklift,
                OperatorID_Web,
                ProductionShift,
                SUM(Forklift_ProcessedDollys) AS Forklift_ProcessedDollys,
                AVG(Forklift_AvgHours) AS Forklift_AvgHours,
                SUM(Web_ProcessedDollys) AS Web_ProcessedDollys,
                AVG(Web_AvgHours) AS Web_AvgHours,
                AVG(OnTimePercent) AS OnTimePercent
            FROM vw_Analytics_OperatorPerformance
            WHERE ProductionDate BETWEEN :date_from AND :date_to
            GROUP BY OperatorID_Forklift, OperatorID_Web, ProductionShift
            ORDER BY Forklift_ProcessedDollys DESC
        """)
        
        result = db.session.execute(query, {"date_from": date_from, "date_to": date_to})
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result.fetchall()]
        
        return jsonify({
            "success": True,
            "data": data,
            "meta": {
                "date_from": date_from,
                "date_to": date_to,
                "note": "Operator IDs are hashed for privacy"
            }
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in operator performance API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analytics_api_bp.route("/monthly-trend")
@login_required
def get_monthly_trend():
    """
    Get monthly trend data for long-term analysis.
    
    Query params:
        - months: Number of months to include (default: 6)
    
    Returns:
        JSON with monthly trend data
    """
    try:
        months = int(request.args.get("months", 6))
        
        query = text("""
            SELECT TOP :months
                ProductionYear,
                ProductionMonth,
                MonthStart,
                TotalDollys,
                CompletedDollys,
                AvgHours_Total,
                TargetAchievementPercent,
                ASN_Count,
                Waybill_Count,
                Both_Count
            FROM vw_Analytics_MonthlyTrend
            ORDER BY ProductionYear DESC, ProductionMonth DESC
        """)
        
        result = db.session.execute(query, {"months": months})
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result.fetchall()]
        
        # Convert datetime objects
        for item in data:
            for key, value in item.items():
                item[key] = _serialize_datetime(value)
        
        return jsonify({
            "success": True,
            "data": data,
            "meta": {
                "months": months
            }
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in monthly trend API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@analytics_api_bp.route("/health")
def health_check():
    """Analytics API health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "HarmonyEcoSystem Analytics API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })
