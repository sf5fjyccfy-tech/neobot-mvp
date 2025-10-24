import httpx
from typing import Dict

WHATSAPP_SERVICE_URL = "http://localhost:3001"

class WhatsAppClient:
    
    async def initiate_connection(self, tenant_id: int) -> Dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{WHATSAPP_SERVICE_URL}/connect",
                    json={"tenant_id": tenant_id}
                )
                return response.json() if response.status_code == 200 else {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def check_status(self, tenant_id: int) -> Dict:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{WHATSAPP_SERVICE_URL}/status/{tenant_id}")
                return response.json() if response.status_code == 200 else {"connected": False}
        except Exception as e:
            return {"connected": False, "error": str(e)}
