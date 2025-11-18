from fastapi import APIRouter, Request, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from app.database import get_db
import os

router = APIRouter()

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "neobot-verify-token-2024")

@router.get("/webhook/facebook")
async def facebook_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """Vérification webhook Facebook"""
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Token invalide")

@router.post("/webhook/facebook")
async def facebook_webhook(request: Request, db: Session = Depends(get_db)):
    """Recevoir messages Facebook"""
    data = await request.json()
    # TODO: Traiter avec MetaService
    return {"status": "ok"}

@router.get("/webhook/instagram")
async def instagram_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """Vérification webhook Instagram"""
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Token invalide")

@router.post("/webhook/instagram")
async def instagram_webhook(request: Request, db: Session = Depends(get_db)):
    """Recevoir messages Instagram"""
    data = await request.json()
    # TODO: Traiter avec MetaService
    return {"status": "ok"}
