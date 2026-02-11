#!/usr/bin/env python3
"""Test the Business Intelligence system without curl"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Wait for backend to start
print("⏳ Waiting for backend to start...")
time.sleep(5)

from app.database import SessionLocal
from app.models import TenantBusinessConfig, BusinessTypeModel, Tenant, Conversation, Message
import json

db = SessionLocal()

print("\n" + "="*60)
print("📊 SYSTEM STATUS CHECK")
print("="*60)

# 1. Check business types
print("\n1️⃣  Business Types:")
types = db.query(BusinessTypeModel).all()
print(f"   ✅ Found {len(types)} types:")
for t in types:
    print(f"      - {t.slug}: {t.name}")

# 2. Check tenant 1
print("\n2️⃣  Tenant 1:")
tenant = db.query(Tenant).filter(Tenant.id == 1).first()
if tenant:
    print(f"   ✅ Tenant: {tenant.name}")
else:
    print(f"   ❌ Tenant 1 not found!")

# 3. Check NéoBot configuration
print("\n3️⃣  NéoBot Configuration:")
config = db.query(TenantBusinessConfig).filter(
    TenantBusinessConfig.tenant_id == 1
).first()

if config:
    print(f"   ✅ Configuration found:")
    print(f"      - Company: {config.company_name}")
    print(f"      - Description: {config.company_description[:50]}...")
    print(f"      - Tone: {config.tone}")
    print(f"      - Selling Focus: {config.selling_focus}")
    
    products = json.loads(config.products_services) if isinstance(config.products_services, str) else config.products_services
    print(f"      - Products: {len(products)} items")
    for p in products:
        print(f"        • {p['name']}: {p['price']} FCFA")
else:
    print(f"   ⚠️  No configuration for Tenant 1")

# 4. Check last conversations
print("\n4️⃣  Last Conversations:")
conversations = db.query(Conversation).filter(
    Conversation.tenant_id == 1
).order_by(Conversation.id.desc()).limit(3).all()

if conversations:
    for conv in conversations:
        print(f"   - Conversation {conv.id}: {conv.customer_name} ({conv.customer_phone})")
else:
    print(f"   ℹ️  No conversations yet")

print("\n" + "="*60)
print("✅ Status Check Complete")
print("="*60 + "\n")

db.close()
