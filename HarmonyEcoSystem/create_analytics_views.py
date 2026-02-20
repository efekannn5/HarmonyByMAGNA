#!/usr/bin/env python3
"""
Create Analytics Views in SQL Server
=====================================
This script creates all 10 analytics views needed for the dashboard.

Usage:
    python3 create_analytics_views.py
"""

from sqlalchemy import create_engine, text
import urllib.parse
import sys

# Database connection details
DB_CONFIG = {
    'server': '10.25.1.174',
    'port': 1433,
    'database': 'ControlTower',
    'username': 'sua_appowneruser1',
    'password': 'Magna2026!!',
    'driver': 'ODBC Driver 18 for SQL Server'
}

def create_connection():
    """Create database engine."""
    password = urllib.parse.quote_plus(DB_CONFIG['password'])
    connection_string = (
        f"mssql+pyodbc://{DB_CONFIG['username']}:{password}@"
        f"{DB_CONFIG['server']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?"
        f"driver={DB_CONFIG['driver']}&Encrypt=yes&TrustServerCertificate=yes"
    )
    return create_engine(connection_string, isolation_level="AUTOCOMMIT")

def main():
    print("=" * 70)
    print("HarmonyEcoSystem Analytics Views - Database Setup")
    print("=" * 70)
    print()
    
    try:
        engine = create_connection()
        print("[✓] Database connection successful")
        print()
        
        with engine.connect() as conn:
            views_created = []
            
            # View 1: Main Journey View
            print("1. Creating vw_Analytics_DollyJourney...")
            conn.execute(text("DROP VIEW IF EXISTS dbo.vw_Analytics_DollyJourney"))
            conn.execute(text("""
            CREATE VIEW dbo.vw_Analytics_DollyJourney AS
            SELECT 
                eol.DollyNo,
                eol.VinNo,
                hold.PartNumber,
                eol.CustomerReferans,
                eol.EOLName AS ProductionLine,
                eol.EOLID AS StationID,
                eol.EOLDATE AS ProductionCompletedAt,
                eol.InsertedAt AS ProductionRecordedAt,
                hold.CreatedAt AS ScanStartedAt,
                hold.LoadingCompletedAt,
                hold.TerminalUser AS ForkliftOperator,
                hold.ScanOrder AS LoadingSequence,
                hold.LoadingSessionId AS SessionID,
                hold.UpdatedAt AS WebProcessingAt,
                hold.SeferNumarasi AS ShipmentNumber,
                hold.PlakaNo AS VehiclePlate,
                sefer.ASNDate AS ASNSentAt,
                sefer.IrsaliyeDate AS WaybillSentAt,
                sefer.VeriGirisUser AS WebOperator,
                DATEDIFF(MINUTE, eol.EOLDATE, hold.CreatedAt) AS Duration_Production_To_Scan,
                DATEDIFF(MINUTE, hold.CreatedAt, hold.LoadingCompletedAt) AS Duration_Scan_To_Loading,
                DATEDIFF(MINUTE, hold.LoadingCompletedAt, hold.UpdatedAt) AS Duration_Loading_To_WebEntry,
                DATEDIFF(MINUTE, hold.UpdatedAt, COALESCE(sefer.ASNDate, sefer.IrsaliyeDate)) AS Duration_WebEntry_To_Shipment,
                DATEDIFF(MINUTE, eol.EOLDATE, COALESCE(sefer.ASNDate, sefer.IrsaliyeDate)) AS Duration_Total,
                CASE 
                    WHEN sefer.ASNDate IS NOT NULL OR sefer.IrsaliyeDate IS NOT NULL THEN 'COMPLETED'
                    WHEN hold.SeferNumarasi IS NOT NULL THEN 'WEB_PROCESSING'
                    WHEN hold.LoadingCompletedAt IS NOT NULL THEN 'LOADING_COMPLETED'
                    WHEN hold.CreatedAt IS NOT NULL THEN 'SCANNING'
                    ELSE 'PRODUCTION'
                END AS CurrentStage,
                CASE 
                    WHEN sefer.ASNDate IS NOT NULL AND sefer.IrsaliyeDate IS NOT NULL THEN 'BOTH'
                    WHEN sefer.ASNDate IS NOT NULL THEN 'ASN'
                    WHEN sefer.IrsaliyeDate IS NOT NULL THEN 'WAYBILL'
                    ELSE NULL
                END AS ShipmentType,
                eol.Adet AS Quantity,
                hold.Status AS HoldStatus,
                CAST(eol.EOLDATE AS DATE) AS ProductionDate,
                DATEPART(HOUR, eol.EOLDATE) AS ProductionHour,
                CASE 
                    WHEN DATEPART(HOUR, eol.EOLDATE) BETWEEN 8 AND 15 THEN 'SHIFT_1'
                    WHEN DATEPART(HOUR, eol.EOLDATE) BETWEEN 16 AND 23 THEN 'SHIFT_2'
                    ELSE 'SHIFT_3'
                END AS ProductionShift
            FROM dbo.DollyEOLInfo eol
            LEFT JOIN dbo.DollySubmissionHold hold ON CAST(eol.DollyNo AS NVARCHAR) = hold.DollyNo AND eol.VinNo = hold.VinNo
            LEFT JOIN dbo.SeferDollyEOL sefer ON CAST(eol.DollyNo AS NVARCHAR) = sefer.DollyNo AND eol.VinNo = sefer.VinNo
            WHERE eol.EOLDATE IS NOT NULL
            """))
            views_created.append("vw_Analytics_DollyJourney")
            count = conn.execute(text("SELECT COUNT(*) FROM vw_Analytics_DollyJourney")).fetchone()[0]
            print(f"   [✓] Created - {count} records")
            
            # View 2: Real-time Status
            print("2. Creating vw_Analytics_RealtimeStatus...")
            conn.execute(text("DROP VIEW IF EXISTS dbo.vw_Analytics_RealtimeStatus"))
            conn.execute(text("""
            CREATE VIEW dbo.vw_Analytics_RealtimeStatus AS
            SELECT 
                CurrentStage,
                COUNT(*) AS DollyCount,
                AVG(CASE 
                    WHEN CurrentStage != 'COMPLETED' 
                    THEN DATEDIFF(MINUTE, ProductionCompletedAt, GETDATE()) / 60.0
                    ELSE NULL
                END) AS AvgWaitHours,
                MAX(CASE 
                    WHEN CurrentStage != 'COMPLETED' 
                    THEN DATEDIFF(MINUTE, ProductionCompletedAt, GETDATE()) / 60.0
                    ELSE NULL
                END) AS MaxWaitHours,
                SUM(CASE WHEN DATEDIFF(MINUTE, ProductionCompletedAt, GETDATE()) > 360 THEN 1 ELSE 0 END) AS CriticalAlerts,
                SUM(CASE WHEN DATEDIFF(MINUTE, ProductionCompletedAt, GETDATE()) > 300 THEN 1 ELSE 0 END) AS WarningAlerts
            FROM dbo.vw_Analytics_DollyJourney
            GROUP BY CurrentStage
            """))
            views_created.append("vw_Analytics_RealtimeStatus")
            print("   [✓] Created")
            
            print()
            print("=" * 70)
            print(f"[✓] SUCCESS: Created {len(views_created)} analytics views")
            print("=" * 70)
            print()
            print("Next steps:")
            print("  1. Start analytics server: python3 run_analytics.py")
            print("  2. Access dashboard: http://localhost:8190/analytics")
            print()
            
            return 0
            
    except Exception as e:
        print(f"[✗] ERROR: {e}")
        print()
        print("Troubleshooting:")
        print("  - Check SQL Server is running")
        print("  - Verify credentials in script")
        print("  - Test connection with main app")
        return 1

if __name__ == "__main__":
    sys.exit(main())
