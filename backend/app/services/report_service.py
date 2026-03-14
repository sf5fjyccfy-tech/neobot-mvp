"""
📋 Report Service
Génère les rapports PDF et Excel avec les analytics
"""
from datetime import datetime
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class ReportService:
    """
    Service pour générer les rapports d'analytics
    """
    
    @staticmethod
    def generate_summary_report(tenant_analytics: Dict) -> str:
        """
        Génère un résumé texte des analytics
        
        Args:
            tenant_analytics: Dict avec toutes les metrics
            
        Returns:
            Texte du rapport
        """
        try:
            report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    RAPPORT D'ANALYTICS NéoBot                              ║
║                    Généré le {datetime.now().strftime("%d/%m/%Y %H:%M")}                        ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 RÉSUMÉ EXÉCUTIF
{'='*80}

💬 CONVERSATIONS
  • Total: {tenant_analytics.get('conversations', {}).get('total_conversations', 0)}
  • Actives: {tenant_analytics.get('conversations', {}).get('active_conversations', 0)}
  • Escaladées: {tenant_analytics.get('conversations', {}).get('escalated_conversations', 0)}
  • Moyenne messages/conversation: {tenant_analytics.get('conversations', {}).get('avg_messages_per_conversation', 0):.2f}

📱 MESSAGES
  • Total: {tenant_analytics.get('conversations', {}).get('total_messages', 0)}
  • Clients: {tenant_analytics.get('conversations', {}).get('customer_messages', 0)}
  • Réponses IA: {tenant_analytics.get('conversations', {}).get('ai_responses', 0)}
  • Taux de réponse: {tenant_analytics.get('conversations', {}).get('response_rate_percent', 0):.1f}%

🎯 CONVERSION
  • Total leads: {tenant_analytics.get('conversion', {}).get('total_leads', 0)}
  • Engagés: {tenant_analytics.get('conversion', {}).get('engaged_conversations', 0)}
  • Taux de conversion: {tenant_analytics.get('conversion', {}).get('conversion_rate_percent', 0):.1f}%

📈 UTILISATION DU PLAN
  • Plan: {tenant_analytics.get('usage', {}).get('plan', 'N/A')}
  • Messages utilisés: {tenant_analytics.get('usage', {}).get('messages_used', 0)}
  • Limite: {tenant_analytics.get('usage', {}).get('messages_limit', 'Illimité')}
  • Taux d'utilisation: {tenant_analytics.get('usage', {}).get('percent_used', 0):.1f}%

🎯 TOP INTENTS
"""
            for intent in tenant_analytics.get('top_intents', [])[:5]:
                report += f"  • {intent.get('intent', 'N/A')}: {intent.get('count', 0)} fois\n"
            
            report += f"""

🚨 ESCALADES
  • Total: {tenant_analytics.get('escalations', {}).get('total_escalations', 0)}
  • Taux: {tenant_analytics.get('escalations', {}).get('escalation_rate_percent', 0):.1f}%
  • Résolues: {tenant_analytics.get('escalations', {}).get('resolved_percent', 0):.1f}%

{'='*80}
Rapport généré automatiquement par NéoBot Analytics
"""
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Erreur generation rapport: {e}")
            return "Erreur lors de la génération du rapport"
    
    @staticmethod
    def generate_html_dashboard(tenant_analytics: Dict) -> str:
        """
        Génère un HTML interactif du dashboard
        
        Args:
            tenant_analytics: Dict avec les metrics
            
        Returns:
            HTML du dashboard
        """
        try:
            conv = tenant_analytics.get('conversations', {})
            usage = tenant_analytics.get('usage', {})
            conversion = tenant_analytics.get('conversion', {})
            
            html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard NéoBot Analytics</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        h1 {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        
        .metric-label {{
            color: #999;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .metric-subvalue {{
            color: #999;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #eee;
            border-radius: 5px;
            overflow: hidden;
            margin-top: 10px;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Dashboard NéoBot Analytics</h1>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">💬 Conversations</div>
                <div class="metric-value">{conv.get('total_conversations', 0)}</div>
                <div class="metric-subvalue">{conv.get('active_conversations', 0)} actives</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">📱 Messages</div>
                <div class="metric-value">{conv.get('total_messages', 0)}</div>
                <div class="metric-subvalue">{conv.get('response_rate_percent', 0):.1f}% réponse IA</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">🎯 Conversion</div>
                <div class="metric-value">{conversion.get('conversion_rate_percent', 0):.1f}%</div>
                <div class="metric-subvalue">{conversion.get('engaged_conversations', 0)} engagés</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">📈 Utilisation Plan</div>
                <div class="metric-value">{usage.get('percent_used', 0):.0f}%</div>
                <div class="metric-subvalue">{usage.get('messages_used', 0)} messages utilisés</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {usage.get('percent_used', 0)}%"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">🚨 Escalades</div>
                <div class="metric-value">{tenant_analytics.get('escalations', {}).get('total_escalations', 0)}</div>
                <div class="metric-subvalue">{tenant_analytics.get('escalations', {}).get('escalation_rate_percent', 0):.1f}% des conversations</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">⏱️ Taux Réponse</div>
                <div class="metric-value">{conv.get('response_rate_percent', 0):.1f}%</div>
                <div class="metric-subvalue">{conv.get('ai_responses', 0)} réponses IA</div>
            </div>
        </div>
        
        <p style="text-align: center; color: white; margin-top: 30px; font-size: 0.9em;">
            Rapport généré le {datetime.now().strftime("%d/%m/%Y à %H:%M")} - NéoBot Analytics v1.0
        </p>
    </div>
</body>
</html>
"""
            return html
            
        except Exception as e:
            logger.error(f"❌ Erreur HTML dashboard: {e}")
            return "<h1>Erreur lors de la génération du dashboard</h1>"
    
    @staticmethod
    def export_to_json(tenant_analytics: Dict) -> Dict:
        """
        Exporte les analytics en JSON
        
        Args:
            tenant_analytics: Dict avec metrics
            
        Returns:
            Dict JSON-compatible
        """
        return {
            "generated_at": datetime.now().isoformat(),
            "analytics": tenant_analytics,
            "version": "1.0"
        }
