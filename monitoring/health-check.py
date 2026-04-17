#!/usr/bin/env python3
"""
NeoBot Server Health Check & Alert System
Monitoring des endpoints critiques avec alertes email via Brevo
Lancé par cron toutes les 5 minutes
"""

import os
import sys
import logging
import httpx
import json
from datetime import datetime, timezone
from pathlib import Path

# Setup logging
LOG_DIR = Path("/root/neobot-mvp/logs/monitoring")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "health-check.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "timpatrick561@gmail.com")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@neobot-ai.com")

# Health check endpoints
HEALTH_CHECKS = {
    "API": "https://api.neobot-ai.com/health",
    "Frontend": "https://neobot-ai.com/",
    "Backend Internal": "http://localhost:8000/health",
}

# Status file pour éviter de spammer emails
STATUS_FILE = LOG_DIR / "last_status.json"


def send_alert_email(subject: str, message: str, is_critical: bool = False) -> bool:
    """Envoyer une alerte email via Brevo"""
    if not BREVO_API_KEY:
        logger.warning("BREVO_API_KEY not configured, skipping email")
        return False
    
    try:
        headers = {
            "api-key": BREVO_API_KEY,
            "Content-Type": "application/json",
        }
        
        payload = {
            "sender": {"name": "NeoBot Monitoring", "email": ADMIN_EMAIL},
            "to": [{"email": ALERT_EMAIL, "name": "Tim"}],
            "subject": subject,
            "htmlContent": f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2 style="color: {'#d32f2f' if is_critical else '#f57c00'};">
                        🚨 {subject}
                    </h2>
                    <p>{message}</p>
                    <p style="color: #666; font-size: 12px; margin-top: 20px;">
                        Timestamp: {datetime.now(timezone.utc).isoformat()}
                    </p>
                </div>
            </body>
            </html>
            """,
        }
        
        with httpx.Client(timeout=10.0) as client:
            r = client.post(
                "https://api.brevo.com/v3/smtp/email",
                headers=headers,
                json=payload,
            )
        
        if r.status_code in [200, 201]:
            logger.info(f"✅ Alert email sent: {subject}")
            return True
        else:
            logger.error(f"❌ Brevo API error: {r.status_code} - {r.text[:200]}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error sending email: {str(e)}")
        return False


def check_endpoint(name: str, url: str, timeout: float = 10.0) -> dict:
    """Vérifier la santé d'un endpoint"""
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url, follow_redirects=True)
        
        is_healthy = r.status_code < 400
        return {
            "name": name,
            "url": url,
            "healthy": is_healthy,
            "status_code": r.status_code,
            "error": None,
        }
    except httpx.TimeoutException:
        return {
            "name": name,
            "url": url,
            "healthy": False,
            "status_code": None,
            "error": "Timeout",
        }
    except Exception as e:
        return {
            "name": name,
            "url": url,
            "healthy": False,
            "status_code": None,
            "error": str(e)[:100],
        }


def load_previous_status() -> dict:
    """Charger le dernier état connu"""
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load previous status: {e}")
    return {}


def save_current_status(status: dict):
    """Sauvegarder l'état actuel"""
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(status, f)
    except Exception as e:
        logger.error(f"Could not save status: {e}")


def main():
    """Exécuter le health check"""
    logger.info("=" * 60)
    logger.info("🔍 Starting health check...")
    
    previous_status = load_previous_status()
    current_status = {}
    all_healthy = True
    
    # Vérifier tous les endpoints
    for name, url in HEALTH_CHECKS.items():
        result = check_endpoint(name, url)
        current_status[name] = result["healthy"]
        
        status_str = "✅ HEALTHY" if result["healthy"] else "❌ DOWN"
        logger.info(f"{status_str} - {name} ({result.get('status_code', 'N/A')})")
        
        if not result["healthy"]:
            all_healthy = False
            
            # Vérifier si c'est une nouvelle défaillance (transition 0→1)
            was_healthy = previous_status.get(name, True)
            if was_healthy:
                # Première fois que c'est down → envoyer alerte
                alert_msg = f"""
                <h3>Service DOWN: {name}</h3>
                <p>URL: {result['url']}</p>
                <p>Status Code: {result.get('status_code', 'Connection failed')}</p>
                <p>Error: {result.get('error', 'Unknown error')}</p>
                <p><strong>Action:</strong> SSH to VPS and check: docker ps && docker logs</p>
                """
                send_alert_email(
                    f"🚨 NeoBot Alert: {name} is DOWN",
                    alert_msg,
                    is_critical=True
                )
    
    # Vérifier les récupérations (transition 1→0)
    for name in previous_status.keys():
        was_healthy = previous_status.get(name, True)
        is_healthy = current_status.get(name, True)
        
        if not was_healthy and is_healthy:
            logger.info(f"✅ {name} RECOVERED")
            send_alert_email(
                f"✅ NeoBot Alert: {name} is BACK ONLINE",
                f"<p>{name} has recovered and is responding normally.</p>"
            )
    
    # Sauvegarder le statut actuel
    save_current_status(current_status)
    
    # Résumé
    if all_healthy:
        logger.info("✅ All systems healthy")
    else:
        logger.warning("⚠️  Some systems are down")
    
    logger.info("=" * 60)
    return 0 if all_healthy else 1


if __name__ == "__main__":
    sys.exit(main())
