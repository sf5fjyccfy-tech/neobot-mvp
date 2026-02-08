#!/usr/bin/env python3
"""
Script de test automatisé pour NéoBot - Standard à utiliser
"""
import requests
import json
import time

class NeoBotTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.test_phone = "+237694256267"
        
    def test_sante(self):
        """Test de santé du backend"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_message(self, message):
        """Test d'un message unique"""
        try:
            response = requests.post(
                f"{self.backend_url}/api/whatsapp/webhook",
                json={"from": self.test_phone, "message": message},
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def test_scenario_complet(self):
        """Test d'un scénario complet de conversation"""
        print("🚀 DÉMARRAGE DU TEST AUTOMATISÉ NÉOBOT")
        print("=" * 50)
        
        # 1. Test santé
        print("1. 🔧 Test santé backend...", end=" ")
        if self.test_sante():
            print("✅")
        else:
            print("❌")
            return
        
        # 2. Scénario de test
        scenarios = [
            # Phase 1: Salutations
            {"message": "Salut", "description": "Salutation simple"},
            {"message": "Bonjour", "description": "Bonjour formel"},
            
            # Phase 2: Demandes restaurant
            {"message": "Menu", "description": "Demande menu"},
            {"message": "Vous avez quoi à manger ?", "description": "Question ouverte"},
            {"message": "Prix du poulet DG", "description": "Demande prix spécifique"},
            {"message": "Horaires", "description": "Demande horaires"},
            
            # Phase 3: Réservation
            {"message": "Je veux réserver", "description": "Début réservation"},
            {"message": "Table pour 4 personnes", "description": "Détails réservation"},
            
            # Phase 4: Livraison
            {"message": "Vous livrez à Bonapriso ?", "description": "Question livraison"},
            
            # Phase 5: Conclusion
            {"message": "Merci", "description": "Remerciement"},
            {"message": "Au revoir", "description": "Fin conversation"}
        ]
        
        print("2. 🧠 Test du Fallback Intelligent...")
        print("-" * 40)
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"{i}. 📨 \"{scenario['message']}\"")
            print(f"   📝 {scenario['description']}")
            
            result = self.test_message(scenario['message'])
            
            if result.get("status") == "success":
                print(f"   💬 {result['response'][:60]}...")
                print(f"   🎯 {result['intent']} (confiance: {result['confidence']:.1f})")
                print(f"   🔧 {result['source']}")
            else:
                print(f"   ❌ Erreur: {result.get('message', 'Unknown')}")
            
            print()
            time.sleep(1)  # Pause entre les tests
        
        print("🎉 TEST TERMINÉ AVEC SUCCÈS !")
        
    def test_performance(self, nb_messages=10):
        """Test de performance avec plusieurs messages"""
        print(f"⚡ TEST PERFORMANCE ({nb_messages} messages)")
        print("-" * 30)
        
        messages = ["Salut", "Menu", "Prix", "Horaires", "Livraison"]
        start_time = time.time()
        
        for i in range(nb_messages):
            msg = messages[i % len(messages)]
            result = self.test_message(msg)
            
            if result.get("status") == "success":
                print(f"  {i+1:2d}. ✅ {msg:15} → {result['source']:8} ({result['confidence']:.1f})")
            else:
                print(f"  {i+1:2d}. ❌ {msg:15} → ERREUR")
        
        end_time = time.time()
        print(f"⏱️  Temps total: {end_time - start_time:.2f}s")
        print(f"📊 Messages/seconde: {nb_messages / (end_time - start_time):.2f}")

if __name__ == "__main__":
    tester = NeoBotTester()
    
    # Menu interactif
    while True:
        print("\n🔧 MENU DE TEST NÉOBOT")
        print("1. Test de santé rapide")
        print("2. Scénario complet")
        print("3. Test performance")
        print("4. Mode interactif")
        print("5. Quitter")
        
        choix = input("\nChoisissez une option (1-5): ").strip()
        
        if choix == "1":
            if tester.test_sante():
                print("✅ Backend opérationnel")
            else:
                print("❌ Backend hors service")
                
        elif choix == "2":
            tester.test_scenario_complet()
            
        elif choix == "3":
            tester.test_performance()
            
        elif choix == "4":
            # Mode interactif
            print("\n💬 MODE INTERACTIF (tapez 'quit' pour sortir)")
            while True:
                message = input("Votre message: ").strip()
                if message.lower() in ['quit', 'exit', 'q']:
                    break
                result = tester.test_message(message)
                if result.get("status") == "success":
                    print(f"🤖 {result['response']}")
                    print(f"   🎯 {result['intent']} | 🔧 {result['source']} | 📊 {result['confidence']:.1f}")
                else:
                    print(f"❌ {result.get('message', 'Erreur')}")
                print()
                
        elif choix == "5":
            print("👋 Au revoir!")
            break
            
        else:
            print("❌ Option invalide")
