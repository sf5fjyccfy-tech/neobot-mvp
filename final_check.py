#!/usr/bin/env python3
"""Quick final verification script"""
import sys
import os
sys.path.insert(0, '/home/tim/neobot-mvp/backend')

from app.database import SessionLocal
from app.models import TenantBusinessConfig, BusinessTypeModel
import json

db = SessionLocal()

print("\n" + "="*60)
print("✅ FINAL VERIFICATION")
print("="*60)

# Check business types
types = db.query(BusinessTypeModel).all()
print(f"\n1️⃣  Business Types: {len(types)} loaded")

# Check tenant 1 config
config = db.query(TenantBusinessConfig).filter(TenantBusinessConfig.tenant_id == 1).first()

if config:
    print(f"\n2️⃣  NéoBot Configuration: ✅ FOUND")
    print(f"     Company: {config.company_name}")
    print(f"     Type: {config.business_type.name if config.business_type else 'N/A'}")
    print(f"     Tone: {config.tone}")
    
    products = json.loads(config.products_services) if isinstance(config.products_services, str) else config.products_services
    print(f"\n     Products ({len(products)}):")
    for p in products:
        print(f"       • {p['name']}: {p['price']} FCFA")
else:
    print(f"\n2️⃣  NéoBot Configuration: ❌ NOT FOUND")
    print("     (Will be created on next backend restart)")

print("\n" + "="*60 + "\n")

db.close()
