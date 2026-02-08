#!/usr/bin/env python3
"""
Client de test pour simuler WhatsApp - Fonctionne sans internet
"""
import requests
import time
import json

BACKEND_URL = "http://localhost:8000"

def test_message(phone, message):
    """Envoie un message au backend"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/whatsapp/webhook",
            json={"from": phone, "message": message},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

def interactive_test():
    """Mode interactif pour tester"""
    print("🚀 CLIENT DE TEST NÉOBOT - Fallback Intelligent")
    print("==============================================")
    print("Le backend fonctionne! Testez avec des messages:")
    print()
    
    phone = "+237694256267"
    
    while True:
        try:
            message = input("💬 Votre message: ").strip()
            if message.lower() in ['quit', 'exit', 'q']:
                break
                
            if not message:
                continue
                
            print("⏳ Envoi...")
            result = test_message(phone, message)
            
            if result.get("status") == "success":
                print(f"🤖 RÉPONSE: {result['response']}")
                print(f"   🎯 Intention: {result['intent']}")
                print(f"   🔧 Source: {result['source']}")
                print(f"   📊 Confiance: {result['confidence']:.1f}")
            else:
                print(f"❌ Erreur: {result.get('message', 'Unknown error')}")
                
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    interactive_test()
