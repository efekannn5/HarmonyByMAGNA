"""
Manager Dashboard Backend API - VIEW Based
FastAPI application with clean endpoints using SQL Views
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Optional

from database import SessionLocal, test_connection
from queries_dashboard import (
    get_dashboard_data,
    get_summary_stats,
    get_group_performance,
    get_operator_stats,
    get_sefer_list,
    get_part_analysis,
    get_hourly_throughput,
    get_dolly_details,
    DashboardData,
    SummaryStats,
    GroupPerformanceItem,
    OperatorItem,
    SeferItem,
    PartItem,
    HourlyItem,
    DollyItem
)

app = FastAPI(
    title="Harmony Manager Dashboard API",
    description="Analytics dashboard for managers - VIEW based queries",
    version="2.0.0"
)

# CORS - tüm kaynaklara izin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Import Chat Router
from endpoints_chat import router as chat_router
app.include_router(chat_router, prefix="/api")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== HEALTH CHECK ====================
@app.on_event("startup")
async def startup_event():
    print("=" * 50)
    print("🚀 Manager Dashboard API v2.0 (VIEW Based)")
    print("📡 Port: 8001")
    if test_connection():
        print("✅ Database connection: OK")
    else:
        print("❌ Database connection: FAILED")
    print("=" * 50)


@app.get("/health")
async def health_check():
    db_ok = test_connection()
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "service": "Manager Dashboard v2.0",
        "port": 8001,
        "version": "VIEW Based"
    }


# ==================== MAIN DASHBOARD ====================
@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    shift: Optional[int] = None,
    min_vin: Optional[int] = None,
    hat: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Ana dashboard verisi - tüm bileşenler
    
    - start_date: Başlangıç tarihi (varsayılan: 7 gün önce)
    - end_date: Bitiş tarihi (varsayılan: bugün)
    - shift: Vardiya filtresi (1=Sabah, 2=Akşam, 3=Gece)
    - min_vin: Minimum VIN sayısı filtresi
    """
    try:
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        if start_date > end_date:
            raise HTTPException(400, "start_date must be before end_date")
        
        return get_dashboard_data(db, start_date, end_date, shift, min_vin, hat)
    
    except Exception as e:
        raise HTTPException(500, f"Dashboard error: {str(e)}")


# ==================== INDIVIDUAL ENDPOINTS ====================
@app.get("/api/summary", response_model=SummaryStats)
async def get_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    shift: Optional[int] = None,
    hat: Optional[str] = None, db: Session = Depends(get_db)
):
    """Özet istatistikler"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=7)
    
    return get_summary_stats(db, start_date, end_date, shift, hat=hat)


@app.get("/api/groups", response_model=list[GroupPerformanceItem])
async def get_groups(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    shift: Optional[int] = None,
    hat: Optional[str] = None, db: Session = Depends(get_db)
):
    """Grup performansları"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=7)
    
    return get_group_performance(db, start_date, end_date, shift, hat=hat)


@app.get("/api/operators", response_model=list[OperatorItem])
async def get_operators(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    shift: Optional[int] = None,
    hat: Optional[str] = None, db: Session = Depends(get_db)
):
    """Operatör istatistikleri"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=7)
    
    return get_operator_stats(db, start_date, end_date, shift, hat=hat)


@app.get("/api/seferler", response_model=list[SeferItem])
async def get_seferler(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    shift: Optional[int] = None,
    limit: int = 30,
    hat: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Sefer listesi"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=7)
    
    return get_sefer_list(db, start_date, end_date, shift, limit, hat=hat)


@app.get("/api/parts", response_model=list[PartItem])
async def get_parts(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    shift: Optional[int] = None,
    hat: Optional[str] = None, db: Session = Depends(get_db)
):
    """Parça analizi"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=7)
    
    return get_part_analysis(db, start_date, end_date, shift, hat=hat)


@app.get("/api/hourly", response_model=list[HourlyItem])
async def get_hourly(
    target_date: Optional[date] = None,
    shift: Optional[int] = None,
    hat: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Saatlik verimlilik"""
    if not target_date:
        target_date = date.today()
    
    return get_hourly_throughput(db, target_date, target_date, shift, hat=hat)


@app.get("/api/dollies", response_model=list[DollyItem])
async def get_dollies(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    shift: Optional[int] = None,
    limit: int = 200,
    hat: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Dolly detayları"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=7)
    
    return get_dolly_details(db, start_date, end_date, shift, limit, hat=hat)


# ==================== RUN ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
