"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    MODÈLES DE DONNÉES - NeobotMVP                           ║
║                    SQLAlchemy ORM Models                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Ce fichier définit la structure des données NeobotMVP.
Il décrit comment les données sont organisées dans PostgreSQL.

ANALOGIE:
  models.py = Le "schéma" d'une maison
  - Tenant = La maison (client/business)
  - Conversation = Une pièce (chat entre client et bot)
  - Message = Un meuble/objet dans la pièce (texte envoyé)
  
Chaque classe Python (Tenant, Conversation, Message) correspond à une table
dans PostgreSQL.
"""

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ IMPORTS                                                                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from sqlalchemy import (
    Column,           # Créer une colonne
    Integer,          # Type entier (1, 2, 3, ...)
    String,           # Type texte/chaîne ("hello", "world", ...)
    Boolean,          # Type booléen (True/False)
    DateTime,         # Type date+heure (2026-02-08 03:47:00)
    Text,             # Type long texte (paragraphes entiers)
    ForeignKey,       # Référence vers une autre table
    Enum as SQLEnum   # Type énumération (choix fixe: "active", "closed", ...)
)
# EXPLICATION:
#   Ces sont les "briques de construction" pour les tables
#   Chaque Column = une colonne dans la table PostgreSQL

from sqlalchemy.orm import relationship
# EXPLICATION:
#   relationship() = crée des liens entre tables
#   Exemple: Tenant a plusieurs Conversations
#   relationship() dit: "Ces deux tables sont liées"

from datetime import datetime, timedelta
# EXPLICATION:
#   datetime = classe pour les dates et heures
#   timedelta = classe pour les durées (ex: 14 jours)

import enum
# EXPLICATION:
#   enum = liste de choix fixes
#   Exemple: PlanType peut être "basique", "standard" ou "pro"
#   Pas d'autres valeurs possibles!

from .database import Base
# EXPLICATION:
#   Base = classe mère créée dans database.py
#   Tous les modèles HÉRITENT de Base
#   GAIN: "Super pouvoirs" SQLAlchemy

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ ENUMS - Énumérations (Choix Fixes)                                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class PlanType(str, enum.Enum):
    """
    Les types de plans disponibles pour les clients.
    
    ANALOGIE: Comme les "paquets" d'une compagnie télécom
      - NEOBOT: Admin interne (gratuit, accès illimité)
      - BASIQUE: Démarrage (2000 messages/mois)
      - STANDARD: Croissance (2500 messages, IA avancée)
      - PRO: Enterprise (4000 messages, support dédié)
    
    UTILISATION:
      tenant.plan = PlanType.BASIQUE  # Au lieu de "basique"
      if tenant.plan == PlanType.STANDARD:  # Vérification sûre
          # Faire quelque chose
    
    GAIN:
      ✓ Pas de typos ("standrd" = erreur détectée)
      ✓ Autocomplete dans l'IDE
      ✓ Type safety
    """
    
    # Format: NAME = "valeur" (la valeur est ce qui va en DB)
    
    NEOBOT = "NEOBOT"
    # Admin interne, accès complet, gratuit
    # Utilisé pour tester, déboguer
    
    BASIQUE = "basique"
    # Premier plan payant
    # 2000 messages WhatsApp/mois
    # 1 canal seulement
    # 14 jours d'essai gratuit
    
    STANDARD = "standard"
    # Plan mid-range
    # 2500 messages WhatsApp/mois
    # Messages illimités sur autres plateformes
    # Jusqu'à 3 canaux
    # IA avancée incluse
    # 7 jours d'essai gratuit
    
    PRO = "pro"
    # Plan Enterprise
    # 4000 messages WhatsApp/mois
    # Canaux illimités
    # Accès API
    # Support dédié
    # Pas d'essai gratuit

class ConversationStatus(str, enum.Enum):
    """
    L'état d'une conversation (chat).
    
    ANALOGIE: Comme les statuts d'un ticket support
      - ACTIVE: Conversation en cours
      - PENDING: En attente de réponse
      - CLOSED: Fermée/terminée
      - ARCHIVED: Archivée (vieille)
    """
    
    ACTIVE = "active"
    # Conversation actuellement en cours
    # Peut recevoir/envoyer des messages
    
    PENDING = "pending"
    # En attente de réponse du bot
    # Ou du client
    
    CLOSED = "closed"
    # Conversation terminée
    # Pas de nouveaux messages
    
    ARCHIVED = "archived"
    # Très ancienne, archivée
    # Peut être restaurée si besoin

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ PLAN LIMITS - Configuration des Plans                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

PLAN_LIMITS = {
    # STRUCTURE: {PlanType: {détails du plan}}
    # En Python pur (pas SQL), pour usage en application
    
    PlanType.NEOBOT: {
        "name": "NéoBot",
        # Nom affiché sur dasboard/emails
        
        "price_fcfa": 0,
        # Prix en FCFA (monnaie locale)
        # NEOBOT = gratuit (admin interne)
        
        "whatsapp_messages": -1,  # -1 = illimité
        # Messages WhatsApp/mois autorisés
        # NEOBOT = illimité
        
        "other_platforms_messages": -1,
        # Messages sur autres plateformes (Telegram, SMS, etc.)
        # NEOBOT = illimité
        
        "channels": -1,
        # Nombre de canaux
        # -1 = illimité (toutes les plateformes)
        
        "features": ["Tout accès", "Support prioritaire"],
        # Liste des features incluses
        # Texte affiché sur le plan
        
        "trial_days": 0
        # Jours d'essai gratuit
        # NEOBOT = 0 (on ne fait pas d'essai admin)
    },
    
    PlanType.BASIQUE: {
        "name": "Basique",
        "price_fcfa": 20000,  # 20 000 FCFA/mois (~30€)
        "whatsapp_messages": 2000,  # 2000 messages/mois
        "other_platforms_messages": 4000,  # 4000 sur autres
        "channels": 1,  # 1 seul canal (ex: WhatsApp)
        "features": [
            "1 canal",
            "Réponses automatiques",
            "Dashboard basique"
        ],
        "trial_days": 14  # 2 semaines d'essai
    },
    
    PlanType.STANDARD: {
        "name": "Standard",
        "price_fcfa": 50000,  # 50 000 FCFA/mois (~75€)
        "whatsapp_messages": 2500,
        "other_platforms_messages": -1,  # Illimité ailleurs
        "channels": 3,  # 3 canaux (WhatsApp, Telegram, etc.)
        "features": [
            "3 canaux",
            "IA avancée",
            "NÉOBRAIN (branche spécialisée)",
            "Analytics/Statistiques"
        ],
        "trial_days": 7  # 1 semaine d'essai
    },
    
    PlanType.PRO: {
        "name": "Pro",
        "price_fcfa": 90000,  # 90 000 FCFA/mois (~135€)
        "whatsapp_messages": 4000,
        "other_platforms_messages": -1,  # Illimité
        "channels": -1,  # Tous les canaux
        "features": [
            "Canaux illimités",
            "CLOSEUR PRO (vente automatique)",
            "API accès complet",
            "Support dédié 24/7"
        ],
        "trial_days": 0  # Pas d'essai (client sérieux)
    }
}

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ MODÈLE 1: TENANT (Client/Business)                                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class Tenant(Base):
    """
    Représente un CLIENT/BUSINESS qui utilise NeobotMVP.
    
    ANALOGIE: Tenant = une "maison" dans une application multi-client
      - La maison a un propriétaire, une adresse, etc.
      - Elle contient des pièces (conversations)
      - Chaque pièce contient des éléments (messages)
    
    EN TERMES SIMPLES:
      - Tenant = une entreprise/commerce qui utilise NéoBot
      - Possède un plan (BASIQUE, STANDARD, PRO)
      - A une limite de messages/mois
      - Peut avoir WhatsApp connecté (Baileys)
    
    EXEMPLE:
      tenant = Tenant(
          name="Alice Cosmetics",
          email="alice@cosmetics.com",
          phone="+237123456789",
          business_type="beauty",
          plan=PlanType.STANDARD
      )
      db.add(tenant)
      db.commit()
      # La table 'tenants' a une nouvelle ligne
    """
    
    # TABLE NAME - Nom de la table PostgreSQL
    __tablename__ = "tenants"
    # Cela crée une table nommée 'tenants' en DB
    
    # ════════════════════════════════════════════════════════
    # COLONNES PRINCIPALES
    # ════════════════════════════════════════════════════════
    
    id = Column(Integer, primary_key=True, index=True)
    # Identifiant unique
    # primary_key=True: C'est la "clé unique" (1, 2, 3, ...)
    # index=True: Créer un index (recherches plus rapides)
    # Type: Entier (auto-incrémenté) 1, 2, 3, ...
    # EN DB: id | name | email | ...
    #       1 | Alice | alice@... | ...
    #       2 | Bob | bob@... | ...
    
    name = Column(String(255), nullable=False)
    # Nom du business (ex: "Alice Cosmetics")
    # String(255): Texte max 255 caractères
    # nullable=False: C'est OBLIGATOIRE (pas de vide)
    # EN DB: name can't be NULL
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    # Email unique (une adresse = un tenant)
    # unique=True: Chaque email ne peut apparaître qu'une fois
    # nullable=False: Obligatoire
    # index=True: Recherches rapides par email
    # UTILITÉ: Chercher un client par email = ultra rapide
    
    phone = Column(String(50), nullable=False)
    # Numéro de téléphone
    # String(50): Texte pour les formats internationaux
    # +237123456789, +2250701020304, etc.
    
    business_type = Column(String(100), default="autre")
    # Type de business (ex: "beauty", "restaurant", "ecommerce")
    # default="autre": Si vide, mettre "autre"
    # UTILITÉ: Personnaliser les réponses par secteur
    
    plan = Column(SQLEnum(PlanType), default=PlanType.BASIQUE, nullable=False)
    # Plan choisi par le client
    # SQLEnum(PlanType): Seulement les valeurs de PlanType
    # default=PlanType.BASIQUE: Plan par défaut au signup
    # nullable=False: Tout client DOIT avoir un plan
    # EN DB: plan IN ('NEOBOT', 'basique', 'standard', 'pro')
    
    # ════════════════════════════════════════════════════════
    # COLONNES WHATSAPP
    # ════════════════════════════════════════════════════════
    
    whatsapp_provider = Column(String(50), default="wasender_api")
    # Quel service ?à utiliser pour WhatsApp
    # Peut être: "wasender_api", "baileys", "twilio", etc.
    # default="wasender_api": Fournisseur par défaut
    # UTILITÉ: Flexibilité pour changer de fournisseur
    
    whatsapp_connected = Column(Boolean, default=False)
    # Est-ce que WhatsApp est avec reconnecté?
    # Boolean: True ou False
    # default=False: Nouvelle départ = pas connecté
    # WHEN TRUE: WhatsApp webhook actif, messages peuvent arriver
    # WHEN FALSE: WhatsApp désactivé
    
    # ════════════════════════════════════════════════════════
    # COLONNES QUOTA (Limitation de messages)
    # ════════════════════════════════════════════════════════
    
    messages_used = Column(Integer, default=0)
    # Nombre de messages utilisés CE MOIS-CI
    # default=0: Nouveau mois = compteur à 0
    # EXEMPLE: Plan BASIQUE limite = 2000
    #          Ce mois-ci utilisé = 1500
    #          Restant = 500 messages
    
    messages_limit = Column(Integer, default=2000)
    # Limite TOTALE de messages/mois
    # default=2000: Par défaut BASIQUE limit
    # CALCUL: Si plan change → update messages_limit
    
    # ════════════════════════════════════════════════════════
    # COLONNES ESSAI (Trial)
    # ════════════════════════════════════════════════════════
    
    is_trial = Column(Boolean, default=True)
    # Est-ce en période d'essai gratuit?
    # True = acccès gratuit (limité dans le temps)
    # False = payant ou après essai
    # UTILITÉ: Tracker si on doit activer la facturation
    
    trial_ends_at = Column(DateTime, nullable=True)
    # Quand l'essai se termine-t-il?
    # DateTime = date + heure (ex: 2026-02-22 03:47:00)
    # nullable=True: Peut être vide (si pas en essai)
    # EXEMPLE: Signup 2026-02-08, essai 14 jours
    #          trial_ends_at = 2026-02-22
    # LOGIQUE: if datetime.now() > trial_ends_at → passer payant
    
    # ════════════════════════════════════════════════════════
    # COLONNES TIMESTAMPS (Quand?)
    # ════════════════════════════════════════════════════════
    
    created_at = Column(DateTime, default=datetime.utcnow)
    # Quand ce client a-t-il été créé?
    # default=datetime.utcnow: Heure actuelle au moment de la création
    # UTC = "Universal Time" (standard international)
    # EXEMPLE: 2026-02-08 03:47:00 UTC
    # UTILITÉ: Savoir quand le customer a rejoint
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
        # ↑ IMPORTANT: updated chaque fois qu'on modifie la ligne
    )
    # Quand ce client a-t-il été modifié POUR LA DERNIÈRE FOIS?
    # onupdate=datetime.utcnow: À chaque modification, mise à jour auto
    # EXEMPLE: créé 2026-02-08, modifié plan le 2026-02-10
    #          created_at = 2026-02-08
    #          updated_at = 2026-02-10
    
    # ════════════════════════════════════════════════════════
    # MÉTHODES (Comportement)
    # ════════════════════════════════════════════════════════
    
    def get_plan_config(self):
        """
        Obtenir la configuration COMPLÈTE du plan.
        
        EXAMPLE:
          tenant = db.query(Tenant).filter(Tenant.id == 1).first()
          config = tenant.get_plan_config()
          # Retourne:
          # {
          #     "name": "Standard",
          #     "price_fcfa": 50000,
          #     "whatsapp_messages": 2500,
          #     "features": ["3 canaux", "IA avancée", ...],
          #     ...
          # }
          
        UTILITÉ: Obtenir tous les détails du plan en une ligne
        """
        return PLAN_LIMITS.get(
            self.plan,  # Chercher la clé self.plan
            PLAN_LIMITS[PlanType.NEOBOT]  # Fallback si pas trouvé
        )
    
    # ════════════════════════════════════════════════════════
    # RELATIONS (Liens vers d'autres tables)
    # ════════════════════════════════════════════════════════
    
    conversations = relationship(
        "Conversation",  # Lier vers la table Conversation
        back_populates="tenant",  # Bidirectionnel
        # ↑ Dans Conversation, il y a: tenant = relationship(..., back_populates="conversations")
    )
    # EXPLICATION:
    #   Un Tenant a PLUSIEURS Conversations
    #   Un Tenant peut avoir 0, 1, 10, 1000 conversations!
    #
    # UTILISATION:
    #   tenant = db.query(Tenant).filter(Tenant.id == 1).first()
    #   all_convos = tenant.conversations  # Liste de Conversation
    #   for conv in all_convos:
    #       print(conv.customer_name)  # "Alice", "Bob", ...
    #
    # BACK_POPULATES:
    #   Cela signifie: "Conversation sait aussi parler du Tenant"
    #   conversation.tenant ← fonctionne aussi!

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ MODÈLE 2: CONVERSATION (Chat)                                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class Conversation(Base):
    """
    Représente une CONVERSATION (chat) entre un client et le bot.
    
    ANALOGIE:
      Tenant = Bureau (la maison)
      Conversation = Une personne qui vient au bureau (visite/chat)
      Message = Ce qu'on dit pendant la visite
    
    UNE CONVERSATION = UN CHAT AVEC UN CLIENT
      - Client: Alice (phone: +237123456789)
      - Conversation: Chat du 8 février 2026
      - Messages: "Bonjour", "Comment ça va?", "Réponse bot", etc.
    
    IMPORTANT:
      - Plusieurs conversations possibles par Tenant
      - Chaque conversation = un client différent
      - Ou un autre chat avec le même client (dates différentes)
    """
    
    __tablename__ = "conversations"
    
    # ════════════════════════════════════════════════════════
    # COLONNES PRINCIPALES
    # ════════════════════════════════════════════════════════
    
    id = Column(Integer, primary_key=True, index=True)
    # ID unique de cette conversation
    
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    # CLEF ÉTRANGÈRE vers Tenant
    # ForeignKey("tenants.id"): Cette conversation APPARTIENT à un Tenant
    # -nullable=False: Chaque conversation DOIT appartenir à un Tenant
    #
    # EXEMPLE:
    #   Tenant id=1 (Alice) a Conversation(tenant_id=1)
    #   Tenant id=2 (Bob) a Conversation(tenant_id=2)
    #   EN DB: Lien créé, intégrité assurée!
    #
    # INTÉGRITÉ REFERENTIELLE:
    #   Si tu tries de créer Conversation(tenant_id=999)
    #   Et Tenant 999 n'existe pas
    #   PostgreSQL dit: "NON! Violation intégrité!"
    #   GAIN: Pas de "conversations orphelines"
    
    customer_phone = Column(String(50), nullable=False)
    # Numéro de téléphone du CLIENT qui chatte
    # EXEMPLE: +237123456789
    # nullable=False: Il faut savoir à qui parler!
    
    customer_name = Column(String(255), nullable=True)
    # Nom du client (optionnel)
    # Peut être vide au début (on ne sait pas son nom)
    # nullable=True: C'est optionnel
    
    channel = Column(String(50), default="whatsapp")
    # Par quel canal le client chatte?
    # "whatsapp" = par WhatsApp
    # "telegram" = par Telegram
    # "sms" = par SMS
    # default="whatsapp": Le canal par défaut
    
    status = Column(String(50), default="active")
    # État de la conversation
    # "active" (en cours) ou "closed" (fermée)
    # default="active": Nouvelle conversation = active
    # UTILITÉ: Pas afficher les conversations fermées en liste
    
    # ════════════════════════════════════════════════════════
    # TIMESTAMPS
    # ════════════════════════════════════════════════════════
    
    created_at = Column(DateTime, default=datetime.utcnow)
    # Quand cette conversation a démarré?
    
    last_message_at = Column(DateTime, default=datetime.utcnow)
    # Quand le dernier message est arrivé?
    # UTILITÉ: Trier les conversations par "nouveau"
    # "Conversations actives récemment" = last_message_at récent
    
    # ════════════════════════════════════════════════════════
    # RELATIONS
    # ════════════════════════════════════════════════════════
    
    tenant = relationship(
        "Tenant",
        back_populates="conversations"
        # ↑ Bidirectionnel: conversation.tenant ET tenant.conversations
    )
    # EXPLICATION:
    #   Chaque Conversation belongsto un Tenant
    #
    # UTILISATION:
    #   conv = db.query(Conversation).filter(Conversation.id == 1).first()
    #   owning_tenant = conv.tenant  # Accès au Tenant propriétaire
    #   print(owning_tenant.name)  # "Alice Cosmetics"
    
    messages = relationship(
        "Message",
        back_populates="conversation"
    )
    # EXPLICATION:
    #   Une Conversation a PLUSIEURS Messages
    #   Relation 1-à-Plusieurs (Conversation:Messages = 1:N)
    #
    # UTILISATION:
    #   all_messages = conv.messages  # Liste de Message
    #   for msg in all_messages:
    #       print(msg.content)  # "Bonjour", "Ca va?", etc.

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ MODÈLE 3: MESSAGE (Texte envoyé)                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class Message(Base):
    """
    Représente UN MESSAGE dans une conversation.
    
    UN MESSAGE = UN TEXTE ENVOYÉ (client ou bot)
    
    ANALOGIA:
      Conversation = Livre
      Message = Une ligne du livre
      
    EXEMPLE DE CONVERSATION:
      Conversation 1 (customer_phone: +237123456789):
        Message: "Bonjour" (direction: "incoming", is_ai: False)
        Message: "Bonjour Ali! Comment puis-je t'aider?" (direction: "outgoing", is_ai: True)
        Message: "Quels sont vos produits?" (direction: "incoming", is_ai: False)
        Message: "Nous avons: ..." (direction: "outgoing", is_ai: True)
    """
    
    __tablename__ = "messages"
    
    # ════════════════════════════════════════════════════════
    # COLONNES
    # ════════════════════════════════════════════════════════
    
    id = Column(Integer, primary_key=True, index=True)
    # ID unique du message
    
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    # CLEF ÉTRANGÈRE vers Conversation
    # Ce message APPARTIENT à une Conversation
    # nullable=False: Chaque message doit être dans une config
    
    content = Column(Text, nullable=False)
    # Le texte du message
    # Text (pas String!): Pour les long textes
    # String = max 255 caractères
    # Text = illimité
    # EXEMPLE: "Bonjour, comment allez-vous?" (100+ caractères possible)
    
    direction = Column(String(20), nullable=False)
    # Qui a envoyé ce message?
    # "incoming" = du client (reçu par nous)
    # "outgoing" = du bot (envoyé par nous)
    # UTILITÉ: Affichage différent (client à gauche, bot à droite)
    
    is_ai = Column(Boolean, default=False)
    # Était-ce une réponse IA?
    # True = Réponse générée par IA (DeepSeek API)
    # False = Réponse manuelle ou template
    # UTILITÉ: Tracker la qualité des réponses IA
    
    created_at = Column(DateTime, default=datetime.utcnow)
    # Quand ce message est arrivé?
    
    # ════════════════════════════════════════════════════════
    # RELATIONS
    # ════════════════════════════════════════════════════════
    
    conversation = relationship(
        "Conversation",
        back_populates="messages"
    )
    # EXPLICATION:
    #   Chaque Message belongsto une Conversation
    #
    # UTILISATION:
    #   msg = db.query(Message).filter(Message.id == 1).first()
    #   parent_conv = msg.conversation  # Parent Conversation
    #   print(parent_conv.customer_name)  # Nom du client

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ RÉSUMÉ: STRUCTURE DES DONNÉES                                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# HIÉRARCHIE (arbre):
# 
#   TENANT (client)
#   ├── Conversation (chat avec client 1)
#   │   ├── Message "Bonjour"
#   │   ├── Message "Comment allez-vous?"
#   │   └── Message "Réponse bot..."
#   ├── Conversation (chat avec client 2)
#   │   ├── Message "Qui êtes-vous?"
#   │   └── Message "Je suis NéoBot..."
#   └── Conversation (chat avec client 1 le jour 2)
#       ├── Message "Bonjour à nouveau"
#       └── Message "Comment ça va?"

# DIAGRAM SQL:
#
#   TENANTS
#   ├─ id (PK)
#   ├─ name
#   ├─ email (unique)
#   ├─ phone
#   ├─ plan (NEOBOT/basique/standard/pro)
#   ├─ whatsapp_connected (true/false)
#   ├─ messages_used
#   ├─ messages_limit
#   ├─ is_trial
#   ├─ trial_ends_at
#   ├─ created_at
#   └─ updated_at
#
#       ↓ (1-à-Plusieurs)
#
#   CONVERSATIONS
#   ├─ id (PK)
#   ├─ tenant_id (FK → TENANTS.id)
#   ├─ customer_phone
#   ├─ customer_name
#   ├─ channel (whatsapp/telegram/sms)
#   ├─ status (active/closed)
#   ├─ created_at
#   └─ last_message_at
#
#       ↓ (1-à-Plusieurs)
#
#   MESSAGES
#   ├─ id (PK)
#   ├─ conversation_id (FK → CONVERSATIONS.id)
#   ├─ content (texte)
#   ├─ direction (incoming/outgoing)
#   ├─ is_ai (true/false)
#   └─ created_at

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ UTILISATION PRATIQUE (Exemples)                                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# CRÉER UN CLIENT:
# ════════════════════════════════════════════════════════════════════════════════
# new_tenant = Tenant(
#     name="Alice Cosmetics",
#     email="alice@cosmetics.com",
#     phone="+237123456789",
#     business_type="beauty",
#     plan=PlanType.STANDARD
# )
# db.add(new_tenant)
# db.commit()
# # INSERT INTO tenants (name, email, phone, ...) VALUES (...)

# OBTENIR TOUTES LES CONVERSATIONS D'UN CLIENT:
# ════════════════════════════════════════════════════════════════════════════════
# tenant = db.query(Tenant).filter(Tenant.id == 1).first()
# conversations = tenant.conversations  # Accès via relation
# # SELECT * FROM conversations WHERE tenant_id = 1

# OBTENIR TOUS LES MESSAGES D'UNE VERSION:
# ════════════════════════════════════════════════════════════════════════════════
# conv = db.query(Conversation).filter(Conversation.id == 5).first()
# messages = conv.messages  # Accès via relation
# # SELECT * FROM messages WHERE conversation_id = 5

# COMPTER MESSAGES UTILISÉS CE MOIS:
# ════════════════════════════════════════════════════════════════════════════════
# from datetime import datetime, timedelta
# from sqlalchemy import and_
#
# tenant = db.query(Tenant).filter(Tenant.id == 1).first()
# month_start = datetime(2026, 2, 1)
# month_end = datetime(2026, 3, 1)
#
# count = db.query(Message).filter(
#     and_(
#         Message.created_at >= month_start,
#         Message.created_at < month_end,
#         Message.direction == "outgoing",  # Seulement les réponses
#         Conversation.tenant_id == tenant.id
#     )
# ).count()
# tenant.messages_used = count
# db.commit()

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ FIN DU FICHIER MODELS.PY                                                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
