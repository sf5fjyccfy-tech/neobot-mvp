"""
Service d'automatisation des achats (IA, hébergement, etc.)
"""

import httpx
import os
from datetime import datetime
from typing import Dict  # ← AJOUT MANQUANT

class AutomationService:
    def __init__(self):
        self.grey_api_key = os.getenv("GREY_API_KEY", "")
        self.grey_card_id = os.getenv("GREY_CARD_ID", "")
        
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY", "sk-442c51d150d2471e87f3913a611737a2")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        
        self.ai_balance_threshold = 1.0
        self.ai_recharge_amount = 5.0
    
    async def check_ai_balance(self) -> float:
        """Vérifier crédit IA restant"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.deepseek.com/user/balance",
                    headers={"Authorization": f"Bearer {self.deepseek_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    balance = data.get("balance_usd", 0)
                    print(f"💰 Crédit IA: ${balance}")
                    return balance
                else:
                    return 0.0
        except Exception as e:
            print(f"⚠️ Erreur check balance: {e}")
            return 0.0
    
    async def auto_recharge_ai(self) -> bool:
        """Recharge automatique crédit IA si nécessaire"""
        balance = await self.check_ai_balance()
        
        if balance < self.ai_balance_threshold:
            print(f"🔄 Balance faible ({balance}$), recharge requise...")
            await self._notify_admin(f"⚠️ ALERTE: Crédit IA faible (${balance}). Rechargez sur platform.deepseek.com")
            return False
        else:
            print(f"✅ Balance IA OK: ${balance}")
            return True
    
    async def _notify_admin(self, message: str):
        """Notifier admin via Telegram"""
        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        telegram_admin_id = os.getenv("TELEGRAM_ADMIN_ID", "")
        
        if not telegram_bot_token or not telegram_admin_id:
            print(f"📢 NOTIFICATION: {message}")
            return
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
                    json={
                        "chat_id": telegram_admin_id,
                        "text": f"🤖 NéoBot Admin\n\n{message}",
                        "parse_mode": "HTML"
                    }
                )
        except Exception as e:
            print(f"⚠️ Erreur notification: {e}")
    
    async def calculate_monthly_costs(self, tenant_count: int, avg_messages_per_tenant: int) -> Dict:
        """Calculer coûts mensuels prévisionnels"""
        
        # Coûts IA (DeepSeek: 0.14$/1M input, 0.28$/1M output)
        total_messages = tenant_count * avg_messages_per_tenant
        total_tokens = total_messages * 250  # 250 tokens par message en moyenne
        
        ai_cost_usd = (total_tokens / 1_000_000) * ((150/250 * 0.14) + (100/250 * 0.28))
        
        # Hébergement (Fly.io gratuit jusqu'à 3 apps)
        hosting_cost_usd = 0 if tenant_count < 100 else 5.0
        
        # Conversion USD → FCFA (1 USD = 615 FCFA)
        usd_to_fcfa = 615
        ai_cost_fcfa = ai_cost_usd * usd_to_fcfa
        hosting_cost_fcfa = hosting_cost_usd * usd_to_fcfa
        total_cost_fcfa = ai_cost_fcfa + hosting_cost_fcfa
        
        # Revenus (plan Basique 20K FCFA/mois)
        revenue_fcfa = tenant_count * 20_000
        
        # Profit
        profit_fcfa = revenue_fcfa - total_cost_fcfa
        margin_percent = (profit_fcfa / revenue_fcfa * 100) if revenue_fcfa > 0 else 0
        
        return {
            "ai_cost_usd": round(ai_cost_usd, 2),
            "ai_cost_fcfa": round(ai_cost_fcfa, 0),
            "hosting_cost_usd": hosting_cost_usd,
            "hosting_cost_fcfa": hosting_cost_fcfa,
            "total_cost_fcfa": round(total_cost_fcfa, 0),
            "revenue_fcfa": revenue_fcfa,
            "profit_fcfa": round(profit_fcfa, 0),
            "margin_percent": round(margin_percent, 1)
        }
