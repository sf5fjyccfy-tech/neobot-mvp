
"""
Package d'initialisation pour forcer le chargement des modèles
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Forcer l'import de tous les modèles
try:
    from .models import Base, Tenant, Conversation, Message
    print("✅ Modèles principaux chargés")
except Exception as e:
    print(f"⚠️  Erreur chargement modèles: {e}")

try:
    from .models_conversation_state import ConversationState
    print("✅ ConversationState chargé")
except ImportError:
    print("ℹ️  ConversationState non trouvé (peut être normal)")
except Exception as e:
    print(f"⚠️  Erreur chargement ConversationState: {e}")
