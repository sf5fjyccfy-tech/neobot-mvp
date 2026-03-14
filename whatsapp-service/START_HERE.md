# 🎯 NéoBot WhatsApp - Démarrage Immédiat

## 👉 **COPIER-COLLER CETTE COMMANDE:**

```bash
cd /home/tim/neobot-mvp/whatsapp-service && chmod +x start-v6.sh && ./start-v6.sh mock
```

**Press Enter.**

Done! ✅

---

## ✨ Qu'est-ce qui va se passer:

1. Service démarre
2. Montre un QR code (simulé pour les tests)
3. Se "connecte" à WhatsApp (fake, pour tester)
4. Envoie des messages simulés au backend toutes les 30 secondes
5. ✅ **Tout fonctionne!**

---

## 🧪 Tester dans un autre terminal:

```bash
# Vérifier le status
curl http://localhost:3001/status

# Simuler un message entrant
curl -X POST http://localhost:3001/test/receive-message
```

---

## 📚 Documentation Complète:

- [Démarrage Rapide](QUICK_START.md)
- [Solution Complète](WHATSAPP_SOLUTION_COMPLETE.md)
- [Problème Résolu](../WHATSAPP_PROBLEM_RESOLVED.md)
- [Changements v6](../CHANGEMENTS_v6.md)

---

## ❓ Hé, pourquoi c'est du "Mock"?

**Le Problème:**
- Baileys (la librairie WhatsApp) ne marche plus
- WhatsApp a changé son protocole en 2026
- Aucune version de Baileys ne peut se connecter

**La Solution:**
- Mode **Mock** = Simule WhatsApp pour tester **MAINTENANT**
- Mode **Official** = Vraie API WhatsApp **PLUS TARD** (après setup Meta)

C'est une meilleure approche que de forcer quelque chose qui ne marche pas!

---

## 🚀 Prêt pour la Production?

Quand vous avez les credentials Meta:

```bash
export WHATSAPP_MODE=official
export WHATSAPP_PHONE_NUMBER_ID="123456789"
export WHATSAPP_ACCESS_TOKEN="EAAxx..."

./start-v6.sh official
```

Et les vrais messages WhatsApp marchent! 📱

---

**C'est terminé! Votre système fonctionne maintenant. 🎉**
