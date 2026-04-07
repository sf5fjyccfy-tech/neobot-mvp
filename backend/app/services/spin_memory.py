"""
Système de mémoire léger pour SPIN Selling
Utilise un cache en mémoire + stockage simple en DB si disponible
"""
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class SpinMemory:
    """Cache mémoire pour suivre les conversations SPIN"""
    
    def __init__(self, db=None):
        self.db = db
        self._memory_cache = {}  # {phone: {data}}
        self._expiry_time = timedelta(minutes=30)  # 30 minutes d'expiration
        
    def get_conversation_state(self, phone: str) -> Dict[str, Any]:
        """Récupère l'état de la conversation"""
        # 1. D'abord en mémoire (ultra-rapide)
        if phone in self._memory_cache:
            data = self._memory_cache[phone]
            if datetime.now() < data.get('expires_at', datetime.now()):
                return data
        
        # 2. Ensuite en DB si disponible
        if self.db:
            try:
                from app.models_conversation_state import ConversationState
                from app.models import Conversation
                
                # Trouver la conversation
                conv = self.db.query(Conversation).filter(
                    Conversation.customer_phone == phone
                ).first()
                
                if conv:
                    state = self.db.query(ConversationState).filter(
                        ConversationState.conversation_id == conv.id
                    ).first()
                    
                    if state:
                        # Convertir en dict et mettre en cache
                        state_data = {
                            'current_stage': state.current_stage,
                            'spin_data': json.loads(state.spin_data) if state.spin_data else {},
                            'last_interaction': state.last_interaction,
                            'business_sector': state.spin_data.get('sector', '') if state.spin_data else '',
                            'expires_at': datetime.now() + self._expiry_time
                        }
                        self._memory_cache[phone] = state_data
                        return state_data
            except Exception as e:
                logger.warning(f"Mémoire DB inaccessible pour {phone}: {e}")
        
        # 3. État par défaut
        return {
            'current_stage': 'initial',
            'spin_data': {},
            'last_interaction': datetime.now(),
            'business_sector': '',
            'expires_at': datetime.now() + self._expiry_time
        }
    
    def update_conversation_state(self, phone: str, updates: Dict[str, Any]):
        """Met à jour l'état de la conversation"""
        current_state = self.get_conversation_state(phone)
        
        # Fusionner les updates
        for key, value in updates.items():
            if key == 'spin_data' and isinstance(value, dict):
                current_state['spin_data'].update(value)
            else:
                current_state[key] = value
        
        current_state['last_interaction'] = datetime.now()
        current_state['expires_at'] = datetime.now() + self._expiry_time
        
        # Mettre en cache
        self._memory_cache[phone] = current_state
        
        # Sauvegarder en DB si disponible (async)
        if self.db:
            try:
                self._save_to_db(phone, current_state)
            except Exception as e:
                logger.warning(f"Sauvegarde DB échouée pour {phone} (non critique): {e}")
    
    def _save_to_db(self, phone: str, state_data: Dict[str, Any]):
        """Sauvegarde asynchrone en DB"""
        from app.models_conversation_state import ConversationState
        from app.models import Conversation
        
        conv = self.db.query(Conversation).filter(
            Conversation.customer_phone == phone
        ).first()
        
        if not conv:
            # Créer une conversation minimale
            conv = Conversation(
                tenant_id=1,  # NéoBot
                customer_phone=phone,
                customer_name=f"Lead {phone[-4:]}",
                channel="whatsapp",
                status="active"
            )
            self.db.add(conv)
            self.db.commit()
            self.db.refresh(conv)
        
        # Chercher ou créer l'état
        db_state = self.db.query(ConversationState).filter(
            ConversationState.conversation_id == conv.id
        ).first()
        
        if not db_state:
            db_state = ConversationState(conversation_id=conv.id)
            self.db.add(db_state)
        
        # Mettre à jour
        db_state.current_stage = state_data.get('current_stage', 'initial')
        db_state.spin_data = json.dumps(state_data.get('spin_data', {}))
        db_state.last_interaction = state_data.get('last_interaction', datetime.now())
        db_state.updated_at = datetime.now()
        
        self.db.commit()
    
    def get_sector_from_history(self, phone: str) -> str:
        """Détecte le secteur depuis l'historique"""
        state = self.get_conversation_state(phone)
        
        # 1. Déjà connu
        if state.get('business_sector'):
            return state['business_sector']
        
        # 2. Détection depuis spin_data
        spin_data = state.get('spin_data', {})
        if 'sector' in spin_data:
            return spin_data['sector']
        
        # 3. Détection intelligente des messages précédents
        messages = spin_data.get('message_history', [])
        for msg in messages[-5:]:  # 5 derniers messages
            msg_lower = msg.lower()
            if any(word in msg_lower for word in ['restaurant', 'manger', 'plat', 'menu']):
                return 'restaurant'
            elif any(word in msg_lower for word in ['boutique', 'magasin', 'acheter', 'produit']):
                return 'boutique'
            elif any(word in msg_lower for word in ['service', 'coiffure', 'nettoyage', 'réparation']):
                return 'service'
        
        return 'autre'
    
    def cleanup_expired(self):
        """Nettoie le cache expiré"""
        now = datetime.now()
        expired = [phone for phone, data in self._memory_cache.items() 
                  if now >= data.get('expires_at', now)]
        for phone in expired:
            del self._memory_cache[phone]

# Instance globale
spin_memory = SpinMemory()
