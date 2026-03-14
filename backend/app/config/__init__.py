import os

# Configuration NéoBot
NEOBOT_TENANT_ID = 1
WHATSAPP_SECRET_KEY = os.getenv("WHATSAPP_WEBHOOK_SECRET") or os.getenv("WHATSAPP_SECRET_KEY") or ""

# Import sales config
from .sales_config import BASIC_PLAN, ACTIVE_PLANS, get_plan, is_plan_active, get_plan_features_formatted

__all__ = ['NEOBOT_TENANT_ID', 'WHATSAPP_SECRET_KEY', 'BASIC_PLAN', 'ACTIVE_PLANS', 'get_plan', 'is_plan_active', 'get_plan_features_formatted']
