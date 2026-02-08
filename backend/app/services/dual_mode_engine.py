"""
Moteur Dual Mode - Version minimale pour intégration progressive
Analyse les conversations et adapte les réponses
"""
from datetime import datetime
from typing import Dict, Any

class DualModeEngine:
    """Moteur léger pour gérer les deux modes"""
    
    def __init__(self):
        self.conversations: Dict[str, Dict] = {}
    
    def analyze_conversation(self, phone: str, tenant_id: str) -> Dict[str, Any]:
        """Analyse basique d'une conversation"""
        conv_id = f"{tenant_id}_{phone}"
        
        if conv_id not in self.conversations:
            return {
                "stage": "new",
                "message_count": 0,
                "is_neobot_admin": "neobot" in phone.lower() or "admin" in phone.lower()
            }
        
        ctx = self.conversations[conv_id]
        msg_count = ctx.get("message_count", 0)
        
        if msg_count == 0:
            stage = "greeting"
        elif msg_count <= 2:
            stage = "engagement"
        elif msg_count <= 5:
            stage = "qualification"
        else:
            stage = "conversation"
        
        return {
            "stage": stage,
            "message_count": msg_count,
            "is_neobot_admin": ctx.get("is_neobot_admin", False)
        }
    
    def track_message(self, phone: str, tenant_id: str, message: str):
        """Suivi des messages"""
        conv_id = f"{tenant_id}_{phone}"
        
        if conv_id not in self.conversations:
            self.conversations[conv_id] = {
                "message_count": 0,
                "first_message": datetime.now(),
                "last_message": datetime.now(),
                "is_neobot_admin": "neobot" in phone.lower() or "admin" in phone.lower()
            }
        
        ctx = self.conversations[conv_id]
        ctx["message_count"] += 1
        ctx["last_message"] = datetime.now()
        
        # Nettoyage automatique (24h)
        self._cleanup()
    
    def _cleanup(self):
        """Nettoie les anciennes conversations"""
        cutoff = datetime.now().timestamp() - 86400  # 24h
        to_remove = []
        
        for conv_id, ctx in self.conversations.items():
            if ctx["last_message"].timestamp() < cutoff:
                to_remove.append(conv_id)
        
        for conv_id in to_remove:
            del self.conversations[conv_id]
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Statistiques des conversations"""
        total = len(self.conversations)
        neobot_convs = sum(1 for ctx in self.conversations.values() 
                          if ctx.get("is_neobot_admin", False))
        
        return {
            "total_conversations": total,
            "neobot_admin_conversations": neobot_convs,
            "client_conversations": total - neobot_convs,
            "active_last_24h": total  # Toutes sont actives grâce au cleanup
        }

# Instance globale pour usage facile
engine = DualModeEngine()
