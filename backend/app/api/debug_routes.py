"""
Routes de debug pour analyser les données reçues
"""
from fastapi import APIRouter, Request
import json

router = APIRouter()

@router.post("/debug/whatsapp")
async def debug_whatsapp(request: Request):
    """Debug des données WhatsApp reçues"""
    print("=" * 50)
    print("🔍 DEBUG WHATSAPP ENDPOINT")
    print("=" * 50)
    
    # Voir les headers
    print("📋 Headers:", dict(request.headers))
    
    # Voir le corps complet
    body_bytes = await request.body()
    print("📦 Body bytes:", body_bytes)
    
    # Essayer de parser comme JSON
    try:
        body_str = body_bytes.decode('utf-8')
        print("📝 Body string:", body_str)
        
        if body_str:
            data = json.loads(body_str)
            print("📨 JSON data:", data)
            print("💬 Message field:", data.get('message', 'NOT FOUND'))
        else:
            print("❌ Body vide")
            
    except json.JSONDecodeError as e:
        print("❌ Erreur JSON:", e)
    except Exception as e:
        print("❌ Autre erreur:", e)
    
    print("=" * 50)
    return {"status": "debugged", "received": body_bytes.decode('utf-8') if body_bytes else "empty"}
