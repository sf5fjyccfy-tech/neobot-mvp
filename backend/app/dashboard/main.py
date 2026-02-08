"""
Dashboard FastAPI - Interface unifiée
"""
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.database import get_db
from app.services.dashboard_service import DashboardService

app = FastAPI(title="NéoBot Dashboard", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration des templates
templates = Jinja2Templates(directory="app/templates")

# ===== ROUTES DASHBOARD =====

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Page d'accueil du dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Dashboard Admin"""
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/client", response_class=HTMLResponse)
async def client_dashboard(request: Request):
    """Dashboard Client"""
    return templates.TemplateResponse("client.html", {"request": request})

# ===== API ENDPOINTS =====

@app.get("/api/admin/overview")
async def admin_overview(db: Session = Depends(get_db)):
    """Vue d'ensemble admin"""
    service = DashboardService(db)
    return {
        "status": "success",
        "data": service.get_admin_overview(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/admin/recent-conversations")
async def admin_recent_conversations(db: Session = Depends(get_db)):
    """Conversations récentes"""
    service = DashboardService(db)
    return {
        "status": "success",
        "data": service.get_recent_conversations(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/admin/client-performance")
async def admin_client_performance(db: Session = Depends(get_db)):
    """Performance des clients"""
    service = DashboardService(db)
    return {
        "status": "success",
        "data": service.get_client_performance(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/admin/analytics/daily")
async def admin_daily_analytics(days: int = 7, db: Session = Depends(get_db)):
    """Analytics quotidiennes"""
    service = DashboardService(db)
    return {
        "status": "success",
        "data": service.get_daily_analytics(days),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/client/{client_id}/overview")
async def client_overview(client_id: int, db: Session = Depends(get_db)):
    """Vue d'ensemble client"""
    service = DashboardService(db)
    overview = service.get_client_overview(client_id)
    
    if not overview:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    return {
        "status": "success",
        "data": overview,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/client/{client_id}/conversations")
async def client_conversations(client_id: int, db: Session = Depends(get_db)):
    """Conversations du client"""
    service = DashboardService(db)
    return {
        "status": "success",
        "data": service.get_client_conversations(client_id),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "dashboard",
        "timestamp": datetime.now().isoformat()
    }

print("🚀 NéoBot Dashboard - Interface unifiée lancée!")
print("📊 Admin: /admin")
print("👤 Client: /client")
print("📈 API: /api/admin/overview")
