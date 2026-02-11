#!/usr/bin/env python3
"""
Test WhatsApp webhook with NéoBot selling message
Tests if business intelligence is working correctly
"""

import sys
import os
import time
import json
import asyncio
import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Wait for backend
print("⏳ Waiting for backend to be ready...")
time.sleep(5)

API_URL = "http://localhost:8000"

async def test_workflow():
    """Run full test workflow"""
    async with httpx.AsyncClient(timeout=10) as client:
        
        print("\n" + "="*70)
        print("🧪 TESTING NEOBOT BUSINESS INTELLIGENCE SYSTEM")
        print("="*70)
        
        # TEST 1: Check business types
        print("\n[TEST 1] Checking business types...")
        try:
            resp = await client.get(f"{API_URL}/api/business/types")
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ Found {data.get('total', 0)} business types")
            else:
                print(f"❌ Failed: {resp.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # TEST 2: Check tenant 1 config
        print("\n[TEST 2] Checking Tenant 1 NéoBot config...")
        try:
            resp = await client.get(f"{API_URL}/api/tenants/1/business/config")
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 'success':
                    print(f"✅ NéoBot configured: {data.get('company_name')}")
                    print(f"   Tone: {data.get('tone')}")
                    print(f"   Focus: {data.get('selling_focus')}")
                    products = data.get('products_services', [])
                    print(f"   Products: {len(products)} items")
                    for p in products:
                        print(f"     • {p['name']}: {p['price']} FCFA")
                else:
                    print(f"⚠️  {data.get('message')}")
            else:
                print(f"❌ Failed: {resp.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # TEST 3: Send message "Neobot c'est combien"
        print("\n[TEST 3] Testing WhatsApp message (pricing question)...")
        try:
            message_data = {
                "from": "+237694256267",
                "text": "Neobot c'est combien ?",
                "senderName": "Patrick",
                "messageKey": {"id": "test123"},
                "timestamp": int(time.time() * 1000),
                "isMedia": False
            }
            
            resp = await client.post(
                f"{API_URL}/api/v1/webhooks/whatsapp",
                json=message_data
            )
            
            if resp.status_code == 200:
                result = resp.json()
                print(f"✅ Message processed:")
                print(f"   Status: {result.get('status')}")
                print(f"   Phone: {result.get('phone')}")
                print(f"   Conversation ID: {result.get('conversation_id')}")
            else:
                print(f"❌ Failed: {resp.status_code}")
                print(f"   Response: {resp.text[:200]}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # TEST 4: Check backend logs for context enrichment
        print("\n[TEST 4] Checking backend logs for context enrichment...")
        try:
            with open('/tmp/backend.log', 'r') as f:
                logs = f.read()
                if 'Enriched prompt with business context' in logs:
                    print("✅ Business context enrichment detected in logs")
                elif 'NéoBot configuration initialized' in logs:
                    print("✅ NéoBot config initialization detected in logs")
                else:
                    print("⚠️  Check logs manually: /tmp/backend.log")
        except Exception as e:
            print(f"⚠️  Could not read logs: {e}")
        
        print("\n" + "="*70)
        print("✅ TEST COMPLETE")
        print("="*70 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(test_workflow())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
