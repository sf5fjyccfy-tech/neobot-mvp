"""
Système d'alertes intelligent pour NéoBot
Génère des notifications proactives pour les clients
"""

from typing import List, Dict
from datetime import datetime, timedelta
from ..models import Tenant

class AlertType:
    WARNING = "warning"   # Jaune - Attention
    DANGER = "danger"     # Rouge - Urgent
    INFO = "info"         # Bleu - Information

class AlertsService:
    """Service de génération d'alertes intelligentes"""
    
    def generate_alerts(self, tenant: Tenant) -> List[Dict]:
        """
        Génère toutes les alertes pertinentes pour un tenant
        
        Returns:
            [
                {
                    "type": "warning" | "danger" | "info",
                    "title": "Titre court",
                    "message": "Message détaillé",
                    "action": "Texte bouton",
                    "action_url": "/url/action",
                    "icon": "emoji"
                }
            ]
        """
        alerts = []
        
        # Alerte 1 : Quota messages
        quota_alert = self._check_quota_alert(tenant)
        if quota_alert:
            alerts.append(quota_alert)
        
        # Alerte 2 : Expiration essai gratuit
        trial_alert = self._check_trial_alert(tenant)
        if trial_alert:
            alerts.append(trial_alert)
        
        # Alerte 3 : WhatsApp déconnecté
        whatsapp_alert = self._check_whatsapp_alert(tenant)
        if whatsapp_alert:
            alerts.append(whatsapp_alert)
        
        # Alerte 4 : Performance IA
        ai_alert = self._check_ai_performance(tenant)
        if ai_alert:
            alerts.append(ai_alert)
        
        return alerts
    
    def _check_quota_alert(self, tenant: Tenant) -> Dict | None:
        """Alerte quota messages"""
        if tenant.messages_limit == 0:
            return None
        
        usage_percent = (tenant.messages_used / tenant.messages_limit) * 100
        remaining = tenant.messages_limit - tenant.messages_used
        
        # Quota épuisé (100%)
        if usage_percent >= 100:
            return {
                "type": AlertType.DANGER,
                "title": "🚨 Quota épuisé",
                "message": f"Vous avez atteint votre limite de {tenant.messages_limit} messages. Votre bot ne répond plus aux nouveaux messages.",
                "action": "Passer au plan supérieur",
                "action_url": "/upgrade",
                "icon": "🚫",
                "priority": 1
            }
        
        # Quota critique (90-99%)
        elif usage_percent >= 90:
            return {
                "type": AlertType.DANGER,
                "title": "⚠️ Quota critique",
                "message": f"Plus que {remaining} messages restants sur {tenant.messages_limit}. Passez au plan supérieur pour éviter une interruption.",
                "action": "Upgrade maintenant",
                "action_url": "/upgrade",
                "icon": "⚠️",
                "priority": 2
            }
        
        # Quota attention (75-89%)
        elif usage_percent >= 75:
            return {
                "type": AlertType.WARNING,
                "title": "📊 Quota élevé",
                "message": f"Vous avez utilisé {tenant.messages_used}/{tenant.messages_limit} messages ({int(usage_percent)}%). Pensez à upgrader.",
                "action": "Voir les plans",
                "action_url": "/plans",
                "icon": "📊",
                "priority": 3
            }
        
        return None
    
    def _check_trial_alert(self, tenant: Tenant) -> Dict | None:
        """Alerte expiration essai gratuit"""
        if not tenant.is_trial or not tenant.trial_ends_at:
            return None
        
        now = datetime.now()
        
        # Essai expiré
        if now > tenant.trial_ends_at:
            return {
                "type": AlertType.DANGER,
                "title": "🔒 Essai expiré",
                "message": "Votre période d'essai gratuit est terminée. Activez un abonnement pour continuer à utiliser NéoBot.",
                "action": "Activer abonnement",
                "action_url": "/payment",
                "icon": "🔒",
                "priority": 1
            }
        
        # Expire dans 1 jour
        delta = tenant.trial_ends_at - now
        days_remaining = delta.days
        hours_remaining = delta.seconds // 3600
        
        if days_remaining == 0 and hours_remaining <= 24:
            return {
                "type": AlertType.DANGER,
                "title": "⏰ Essai expire demain",
                "message": f"Votre essai gratuit expire dans {hours_remaining}h. Activez votre abonnement dès maintenant.",
                "action": "Activer maintenant",
                "action_url": "/payment",
                "icon": "⏰",
                "priority": 2
            }
        
        # Expire dans 2-3 jours
        elif days_remaining <= 2:
            return {
                "type": AlertType.WARNING,
                "title": "📅 Essai se termine bientôt",
                "message": f"Plus que {days_remaining} jours d'essai gratuit. Préparez votre abonnement.",
                "action": "Voir les plans",
                "action_url": "/plans",
                "icon": "📅",
                "priority": 3
            }
        
        return None
    
    def _check_whatsapp_alert(self, tenant: Tenant) -> Dict | None:
        """Alerte WhatsApp déconnecté"""
        plan_config = tenant.get_plan_config()
        
        # WhatsApp pas encore configuré
        if not tenant.whatsapp_connected:
            if plan_config.get("requires_client_tokens"):
                return {
                    "type": AlertType.WARNING,
                    "title": "📱 WhatsApp non configuré",
                    "message": "Votre bot n'est pas encore connecté à WhatsApp. Configurez vos tokens pour activer le service.",
                    "action": "Configurer WhatsApp",
                    "action_url": "/whatsapp",
                    "icon": "📱",
                    "priority": 4
                }
            else:
                return {
                    "type": AlertType.INFO,
                    "title": "📱 Scannez le QR Code",
                    "message": "Connectez votre WhatsApp en scannant le QR code avec votre téléphone.",
                    "action": "Voir QR Code",
                    "action_url": "/whatsapp",
                    "icon": "📱",
                    "priority": 4
                }
        
        return None
    
    def _check_ai_performance(self, tenant: Tenant) -> Dict | None:
        """Alerte performance IA (optionnel)"""
        # Si le tenant utilise beaucoup de messages mais a peu de conversations
        # → Possible problème de configuration
        
        if tenant.messages_used > 500:  # Seuil arbitraire
            # TODO: Implémenter logique basée sur ratio messages/conversations
            pass
        
        return None
    
    def get_priority_alerts(self, tenant: Tenant, max_alerts: int = 3) -> List[Dict]:
        """
        Récupère les X alertes les plus prioritaires
        
        Args:
            tenant: Client concerné
            max_alerts: Nombre max d'alertes à retourner
        
        Returns:
            Liste triée par priorité
        """
        alerts = self.generate_alerts(tenant)
        
        # Trier par priorité (1 = plus urgent)
        sorted_alerts = sorted(alerts, key=lambda x: x.get("priority", 99))
        
        return sorted_alerts[:max_alerts]
