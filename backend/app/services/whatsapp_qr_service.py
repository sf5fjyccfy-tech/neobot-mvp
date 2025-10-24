# backend/app/services/whatsapp_qr_service.py

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import Tenant, WhatsAppSession, Message

logger = logging.getLogger(__name__)

class WhatsAppQRService:
    """Service WhatsApp avec connexion QR et limite cachée"""
    
    def __init__(self, db: Session):
        self.db = db
        self.DAILY_MESSAGE_LIMIT = 120  # Limite cachée
        self.sessions = {}  # Cache des sessions actives
    
    async def initiate_qr_connection(self, tenant_id: int) -> Dict[str, Any]:
        """Initier une connexion QR pour un tenant"""
        try:
            # Vérifier si session existe déjà
            existing_session = self.db.query(WhatsAppSession).filter(
                WhatsAppSession.tenant_id == tenant_id
            ).first()
            
            if existing_session and existing_session.is_connected:
                return {
                    "status": "already_connected",
                    "phone_number": existing_session.phone_number,
                    "connected_since": existing_session.connected_at
                }
            
            # Générer nouveau QR code
            qr_code = await self._generate_qr_code(tenant_id)
            
            # Créer ou mettre à jour session
            if existing_session:
                existing_session.qr_code = qr_code
                existing_session.is_connected = False
                existing_session.updated_at = datetime.now()
            else:
                session = WhatsAppSession(
                    tenant_id=tenant_id,
                    provider="baileys_qr",
                    qr_code=qr_code,
                    is_connected=False
                )
                self.db.add(session)
            
            self.db.commit()
            
            return {
                "status": "qr_generated",
                "qr_code": qr_code,
                "instructions": "Scannez ce QR code avec votre WhatsApp pour connecter votre bot"
            }
            
        except Exception as e:
            logger.error(f"Erreur génération QR tenant {tenant_id}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def send_message(self, tenant_id: int, to_phone: str, message: str) -> Dict[str, Any]:
        """Envoyer un message avec vérification limite cachée"""
        try:
            # Vérifier limite quotidienne
            if not await self._check_daily_limit(tenant_id):
                # Ne pas révéler la vraie raison - message générique
                return {
                    "status": "temporary_unavailable",
                    "error": "Service temporairement indisponible. Réessayez plus tard."
                }
            
            # Vérifier que la session est connectée
            session = await self._get_active_session(tenant_id)
            if not session:
                return {
                    "status": "not_connected",
                    "error": "Bot non connecté. Veuillez scanner le QR code."
                }
            
            # Envoyer le message via Baileys
            result = await self._send_via_baileys(session, to_phone, message)
            
            if result["status"] == "sent":
                # Incrémenter compteur quotidien
                await self._increment_daily_counter(tenant_id)
                
                # Logger pour monitoring
                logger.info(f"Message envoyé - Tenant {tenant_id} - Quota utilisé: {await self._get_daily_usage(tenant_id)}/120")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur envoi message tenant {tenant_id}: {e}")
            return {
                "status": "error",
                "error": "Erreur lors de l'envoi du message"
            }
    
    async def get_connection_status(self, tenant_id: int) -> Dict[str, Any]:
        """Obtenir le statut de connexion"""
        try:
            session = self.db.query(WhatsAppSession).filter(
                WhatsAppSession.tenant_id == tenant_id
            ).first()
            
            if not session:
                return {
                    "status": "no_session",
                    "connected": False,
                    "qr_needed": True
                }
            
            if session.is_connected:
                # Vérifier usage quotidien (sans révéler la limite)
                daily_usage = await self._get_daily_usage(tenant_id)
                usage_percentage = (daily_usage / self.DAILY_MESSAGE_LIMIT) * 100
                
                # Alertes subtiles selon l'usage
                warning = None
                if usage_percentage > 90:
                    warning = "Utilisation intensive détectée. Le service peut être temporairement ralenti."
                elif usage_percentage > 70:
                    warning = "Forte activité aujourd'hui. Performances optimales garanties."
                
                return {
                    "status": "connected",
                    "connected": True,
                    "phone_number": session.phone_number,
                    "connected_since": session.connected_at,
                    "last_activity": session.last_activity,
                    "warning": warning,
                    "usage_indicator": "normal" if usage_percentage < 70 else "high"
                }
            else:
                return {
                    "status": "disconnected",
                    "connected": False,
                    "qr_code": session.qr_code,
                    "qr_needed": True
                }
                
        except Exception as e:
            logger.error(f"Erreur statut connexion tenant {tenant_id}: {e}")
            return {
                "status": "error",
                "error": "Impossible de vérifier le statut"
            }
    
    async def _check_daily_limit(self, tenant_id: int) -> bool:
        """Vérifier si la limite quotidienne est atteinte (fonction cachée)"""
        daily_usage = await self._get_daily_usage(tenant_id)
        return daily_usage < self.DAILY_MESSAGE_LIMIT
    
    async def _get_daily_usage(self, tenant_id: int) -> int:
        """Obtenir l'usage quotidien actuel"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Compter les messages sortants d'aujourd'hui
        count = self.db.query(Message).join(
            Message.conversation
        ).filter(
            Message.direction == "out",
            Message.created_at >= today_start,
            Message.created_at < today_end,
            Message.conversation.has(tenant_id=tenant_id)
        ).count()
        
        return count
    
    async def _increment_daily_counter(self, tenant_id: int):
        """Incrémenter le compteur quotidien (déjà fait par le count en DB)"""
        # Le compteur est automatique via les messages en DB
        # Optionnel: cache Redis pour performance
        pass
    
    async def _generate_qr_code(self, tenant_id: int) -> str:
        """Générer un QR code via Baileys"""
        try:
            # Simulation - dans la vraie implémentation, appel Baileys
            # qui retourne le QR code en base64 ou URL
            
            import uuid
            session_id = str(uuid.uuid4())
            
            # QR code contiendra les infos de session Baileys
            qr_data = f"baileys_session_{tenant_id}_{session_id}"
            
            # Dans la vraie implémentation:
            # qr_code = await baileys_client.generate_qr(session_id)
            
            return f"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            
        except Exception as e:
            logger.error(f"Erreur génération QR: {e}")
            return None
    
    async def _get_active_session(self, tenant_id: int) -> Optional[WhatsAppSession]:
        """Obtenir la session active pour un tenant"""
        return self.db.query(WhatsAppSession).filter(
            WhatsAppSession.tenant_id == tenant_id,
            WhatsAppSession.is_connected == True
        ).first()
    
    async def _send_via_baileys(self, session: WhatsAppSession, to_phone: str, message: str) -> Dict[str, Any]:
        """Envoyer message via Baileys (implémentation simulée)"""
        try:
            # Dans la vraie implémentation:
            # result = await baileys_client.send_message(session.session_id, to_phone, message)
            
            # Simulation d'envoi réussi
            await asyncio.sleep(0.1)  # Simule latence réseau
            
            # Mettre à jour dernière activité
            session.last_activity = datetime.now()
            self.db.commit()
            
            return {
                "status": "sent",
                "message_id": f"wa_msg_{int(datetime.now().timestamp())}",
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Erreur envoi Baileys: {e}")
            return {
                "status": "failed",
                "error": "Échec d'envoi via WhatsApp"
            }
    
    async def handle_qr_scan_success(self, tenant_id: int, phone_number: str):
        """Callback quand le QR code est scanné avec succès"""
        try:
            session = self.db.query(WhatsAppSession).filter(
                WhatsAppSession.tenant_id == tenant_id
            ).first()
            
            if session:
                session.is_connected = True
                session.phone_number = phone_number
                session.connected_at = datetime.now()
                session.last_activity = datetime.now()
                session.qr_code = None  # Plus besoin du QR
                
                self.db.commit()
                
                logger.info(f"Session connectée avec succès - Tenant {tenant_id} - Numéro {phone_number}")
                
                # Optionnel: envoyer message de confirmation au tenant
                await self._notify_connection_success(tenant_id)
                
        except Exception as e:
            logger.error(f"Erreur confirmation connexion QR: {e}")
    
    async def _notify_connection_success(self, tenant_id: int):
        """Notifier le tenant que la connexion est réussie"""
        # Implémentation: email, notification dashboard, etc.
        pass
    
    async def monitor_session_health(self, tenant_id: int):
        """Surveiller la santé de la session (tâche background)"""
        try:
            session = await self._get_active_session(tenant_id)
            if not session:
                return
            
            # Vérifier si la session est toujours active
            # Dans la vraie implémentation: ping Baileys
            is_alive = await self._ping_baileys_session(session)
            
            if not is_alive:
                # Marquer comme déconnectée
                session.is_connected = False
                session.last_activity = datetime.now()
                self.db.commit()
                
                logger.warning(f"Session déconnectée détectée - Tenant {tenant_id}")
                
                # Optionnel: notifier le tenant
                await self._notify_disconnection(tenant_id)
                
        except Exception as e:
            logger.error(f"Erreur monitoring session {tenant_id}: {e}")
    
    async def _ping_baileys_session(self, session: WhatsAppSession) -> bool:
        """Vérifier si la session Baileys est encore active"""
        # Implémentation simulée
        # Dans la vraie version: test de ping via Baileys
        return True
    
    async def _notify_disconnection(self, tenant_id: int):
        """Notifier une déconnexion au tenant"""
        # Email, notification dashboard, etc.
        pass

# Service d'administration pour monitoring
class WhatsAppAdminService:
    """Service admin pour surveiller l'usage et détecter les abus"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Statistiques globales d'usage (pour admin uniquement)"""
        today = datetime.now().date()
        
        # Stats par tenant
        tenant_stats = []
        tenants = self.db.query(Tenant).filter(Tenant.is_active == True).all()
        
        for tenant in tenants:
            daily_usage = await self._get_tenant_daily_usage(tenant.id)
            
            tenant_stats.append({
                "tenant_id": tenant.id,
                "tenant_name": tenant.name,
                "daily_usage": daily_usage,
                "usage_percentage": (daily_usage / 120) * 100,
                "plan": tenant.plan.value,
                "risk_level": "high" if daily_usage > 100 else "normal"
            })
        
        return {
            "date": today,
            "total_tenants": len(tenants),
            "tenant_stats": tenant_stats,
            "high_usage_tenants": [t for t in tenant_stats if t["risk_level"] == "high"]
        }
    
    async def _get_tenant_daily_usage(self, tenant_id: int) -> int:
        """Usage quotidien d'un tenant spécifique"""
        service = WhatsAppQRService(self.db)
        return await service._get_daily_usage(tenant_id)
    
    async def flag_suspicious_activity(self) -> list:
        """Détecter les activités suspectes"""
        suspicious = []
        tenants = self.db.query(Tenant).filter(Tenant.is_active == True).all()
        
        for tenant in tenants:
            usage = await self._get_tenant_daily_usage(tenant.id)
            
            if usage > 110:  # 90%+ de la limite
                suspicious.append({
                    "tenant_id": tenant.id,
                    "tenant_name": tenant.name,
                    "daily_usage": usage,
                    "risk": "approaching_limit",
                    "action": "monitor_closely"
                })
        
        return suspicious