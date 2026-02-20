#!/usr/bin/env python3
"""
Test script for /api/yuzde endpoint
Dolly dolma durumunu gösterir
"""
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from datetime import datetime
import json

app = create_app()

with app.app_context():
    # SQL query: Her EOL grubu için dolly analizi
    query = """
    WITH CurrentDollys AS (
        -- Her EOL için en son dolly'yi bul
        SELECT 
            EOLName,
            DollyNo,
            COUNT(VinNo) as CurrentVinCount,
            MAX(InsertedAt) as LastInsertTime,
            MAX(VinNo) as LastVin
        FROM DollyEOLInfo
        GROUP BY EOLName, DollyNo
    ),
    DollyCapacities AS (
        -- Her dolly'nin kaç VIN içerdiğini hesapla
        SELECT 
            EOLName,
            DollyNo,
            COUNT(VinNo) as VinCount
        FROM DollyEOLInfo
        GROUP BY EOLName, DollyNo
    ),
    MaxCapacities AS (
        -- Her EOL grubu için maksimum VIN kapasitesini bul
        SELECT 
            EOLName,
            MAX(VinCount) as MaxVinCapacity,
            AVG(CAST(VinCount as FLOAT)) as AvgVinCapacity,
            COUNT(DISTINCT DollyNo) as TotalDollys
        FROM DollyCapacities
        GROUP BY EOLName
    )
    SELECT 
        cd.EOLName,
        cd.DollyNo as CurrentDolly,
        cd.CurrentVinCount,
        mc.MaxVinCapacity,
        mc.AvgVinCapacity,
        mc.TotalDollys,
        cd.LastVin,
        cd.LastInsertTime,
        -- Yüzde hesapla
        CASE 
            WHEN mc.MaxVinCapacity > 0 THEN 
                CAST(cd.CurrentVinCount as FLOAT) / CAST(mc.MaxVinCapacity as FLOAT) * 100
            ELSE 0
        END as FillingPercentage
    FROM CurrentDollys cd
    LEFT JOIN MaxCapacities mc ON cd.EOLName = mc.EOLName
    WHERE cd.LastInsertTime = (
        -- Sadece en son dolly'leri getir
        SELECT MAX(LastInsertTime) 
        FROM CurrentDollys cd2 
        WHERE cd2.EOLName = cd.EOLName
    )
    ORDER BY cd.EOLName, cd.DollyNo
    """
    
    result = db.session.execute(db.text(query)).fetchall()
    
    print("\n" + "="*80)
    print("🎯 DOLLY DOLMA DURUMU RAPORU")
    print("="*80)
    print(f"⏰ Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    if not result:
        print("\n⚠️  Henüz veri yok!\n")
        sys.exit(0)
    
    eol_groups = []
    summary = {
        "total_active_dollys": 0,
        "filling_dollys": 0,
        "full_dollys": 0,
        "empty_dollys": 0
    }
    
    for row in result:
        eol_name = row[0]
        current_dolly = row[1]
        current_vin_count = row[2]
        max_capacity = row[3]
        avg_capacity = row[4]
        total_dollys = row[5]
        last_vin = row[6]
        last_insert_time = row[7]
        filling_percentage = row[8]
        
        # Durum hesapla
        remaining_vins = max_capacity - current_vin_count
        
        # Status belirleme
        if filling_percentage >= 100:
            status = "DOLU ✅"
            emoji = "🔴"
            message = "Dolly DOLDU - Yeni dolly bekleniyor..."
            can_scan = False
            summary["full_dollys"] += 1
        elif filling_percentage >= 90:
            status = "NEREDEYSE DOLU ⚠️"
            emoji = "🟠"
            message = f"Dikkat! {remaining_vins} VIN kaldı"
            can_scan = True
            summary["filling_dollys"] += 1
        elif filling_percentage > 0:
            status = "DOLUYOR 📦"
            emoji = "🟢"
            message = f"Dolmasına {remaining_vins} VIN kaldı"
            can_scan = True
            summary["filling_dollys"] += 1
        else:
            status = "BOŞ 📭"
            emoji = "⚪"
            message = "Boş dolly - İlk VIN bekleniyor"
            can_scan = True
            summary["empty_dollys"] += 1
        
        summary["total_active_dollys"] += 1
        
        # Konsol çıktısı
        print(f"\n{emoji} {eol_name}")
        print(f"   └─ Dolly: {current_dolly}")
        print(f"   └─ Durum: {status}")
        print(f"   └─ VIN Sayısı: {current_vin_count}/{max_capacity} ({filling_percentage:.1f}%)")
        print(f"   └─ Mesaj: {message}")
        print(f"   └─ Son VIN: {last_vin}")
        print(f"   └─ Tarama: {'✅ Açık' if can_scan else '🔒 Kapalı'}")
        print(f"   └─ Ortalama Kapasite: {avg_capacity:.1f} VIN")
        print(f"   └─ Toplam Dolly Sayısı: {total_dollys}")
        
        # JSON için kaydet
        eol_groups.append({
            "eol_name": eol_name,
            "current_dolly": current_dolly,
            "current_vin_count": current_vin_count,
            "max_vin_capacity": max_capacity,
            "avg_vin_capacity": round(avg_capacity, 2),
            "total_dollys_history": total_dollys,
            "filling_percentage": round(filling_percentage, 2),
            "remaining_vins": remaining_vins,
            "status": status,
            "message": message,
            "last_vin": last_vin,
            "last_insert_time": last_insert_time.isoformat() if last_insert_time else None,
            "can_scan": can_scan
        })
    
    print("\n" + "="*80)
    print("📊 ÖZET")
    print("="*80)
    print(f"Toplam Aktif Dolly: {summary['total_active_dollys']}")
    print(f"Doluyor: {summary['filling_dollys']} | Dolu: {summary['full_dollys']} | Boş: {summary['empty_dollys']}")
    print("="*80)
    
    # JSON formatında da kaydet
    output = {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "eol_groups": eol_groups,
        "summary": summary
    }
    
    print("\n\n📄 JSON RESPONSE:")
    print(json.dumps(output, indent=2, ensure_ascii=False))
    print("\n")
