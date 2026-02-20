"""
Harmony Control Tower - FastAPI Backend
Real-time dashboard with WebSocket support
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List
import json

from database import get_db, test_connection
from queries import get_dashboard_data
from models import DashboardData

load_dotenv()

# FastAPI app
app = FastAPI(
    title="Harmony Control Tower API",
    description="Real-time dashboard for Magna dolly logistics",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Harmony Control Tower",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = test_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard(db: Session = Depends(get_db)):
    """Get complete dashboard data"""
    data = get_dashboard_data(db)
    return data

# ==================== WEBSOCKET ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    refresh_interval = int(os.getenv("REFRESH_INTERVAL", 3))
    
    try:
        while True:
            # Get fresh data from database
            db = next(get_db())
            try:
                data = get_dashboard_data(db)
                
                # Convert Pydantic models to dict for JSON serialization (mode='json' for datetime)
                message = {
                    "type": "dashboard_update",
                    "data": {
                        "queue_status": data["queue_status"].model_dump(mode='json'),
                        "eol_distribution": [item.model_dump(mode='json') for item in data["eol_distribution"]],
                        "loading_sessions": [item.model_dump(mode='json') for item in data["loading_sessions"]],
                        "daily_statistics": data["daily_statistics"].model_dump(mode='json'),
                        "recent_activities": [item.model_dump(mode='json') for item in data["recent_activities"]],
                        "part_summaries": [item.model_dump(mode='json') for item in data["part_summaries"]],
                        "process_timeline": data["process_timeline"],
                        "performance_metrics": data["performance_metrics"],
                        "active_dolly_filling": data["active_dolly_filling"],
                        "shift_statistics": data["shift_statistics"],
                        "part_based_summary": data["part_based_summary"],
                        "line_visualization": data["line_visualization"],
                        "last_updated": data["last_updated"].isoformat()
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                # Use jsonable_encoder to handle datetime objects and other types
                from fastapi.encoders import jsonable_encoder
                await websocket.send_json(jsonable_encoder(message))
                
            finally:
                db.close()
            
            # Wait for next refresh
            await asyncio.sleep(refresh_interval)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# ==================== STARTUP EVENT ====================

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    print("=" * 50)
    print("Harmony Control Tower - Starting Up")
    print("=" * 50)
    
    # Test database connection
    if test_connection():
        print("Database connection: OK")
    else:
        print("Database connection: FAILED")
        print("WARNING: Dashboard will not work without database!")
    
    print(f"Refresh interval: {os.getenv('REFRESH_INTERVAL', 3)} seconds")
    print(f"CORS origins: {os.getenv('CORS_ORIGINS', '*')}")
    print("=" * 50)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", 8000)),
        reload=True
    )
