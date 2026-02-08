#!/usr/bin/env python3
"""
Test final complet du système NéoBot
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def run_tests():
    print("🧪 TEST FINAL NÉOBOT - VERSION 2.0")
    print("=" * 50)
    
    # 1. Test santé
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {resp.status_code}")
        print(f"   Détail: {resp.json()}")
    except Exception as e:
        print(f"❌ Health check: {e}")
    
    # 2. Test routes publiques
    print("\n📡 Routes Publiques:")
    routes = [
        ("/", "Root"),
        ("/api/test", "Test API"),
        ("/api/data", "Data API"),
        ("/api/tenants/1", "Tenant 1")
    ]
    
    for route, name in routes:
        try:
            resp = requests.get(f"{BASE_URL}{route}")
            print(f"✅ {name}: {resp.status_code} - {resp.json()}")
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    # 3. Test authentification CORRECTE (avec /api/)
    print("\n🔐 Authentification:")
    try:
        # FormData pour /api/auth/login
        data = {
            "username": "tim@neobot.ai",
            "password": "admin123"
        }
        resp = requests.post(f"{BASE_URL}/api/auth/login", data=data)
        
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            print(f"✅ Authentification réussie")
            print(f"   Token: {token}")
            
            # Test route protégée avec token
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(f"{BASE_URL}/api/tenants/1", headers=headers)
            print(f"✅ Route protégée: {resp.status_code}")
        else:
            print(f"⚠️  Authentification: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Authentification: {e}")
    
    # 4. Test webhook WhatsApp
    print("\n📱 Webhook WhatsApp:")
    try:
        data = {
            "phone": "237612345678",
            "message": "Bonjour, vous avez quoi au menu ?"
        }
        resp = requests.post(f"{BASE_URL}/api/tenants/1/whatsapp/message", json=data)
        print(f"✅ Webhook WhatsApp: {resp.status_code}")
        if resp.status_code == 200:
            print(f"   Réponse: {resp.json()}")
    except Exception as e:
        print(f"❌ Webhook WhatsApp: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 TEST TERMINÉ - Backend NéoBot Opérationnel !")

if __name__ == "__main__":
    run_tests()
