from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

router = APIRouter()

# Configuration des templates
templates = Jinja2Templates(directory="app/dashboard/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Page principale du dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/dashboard/whatsapp", response_class=HTMLResponse)
async def whatsapp_page(request: Request):
    """Page de gestion WhatsApp"""
    return templates.TemplateResponse("whatsapp.html", {"request": request})

@router.get("/dashboard/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Page analytics détaillées"""
    return templates.TemplateResponse("analytics.html", {"request": request})

@router.get("/dashboard/conversations", response_class=HTMLResponse)
async def conversations_page(request: Request):
    """Page des conversations"""
    return templates.TemplateResponse("conversations.html", {"request": request})

@router.get("/dashboard/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Page des paramètres"""
    return templates.TemplateResponse("settings.html", {"request": request})
