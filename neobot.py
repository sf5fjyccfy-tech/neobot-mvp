#!/usr/bin/env python3
"""
neobot.py — CLI complet pour piloter NéoBot
Usage: python neobot.py <commande> [options]
"""

import sys
import json
import time
import argparse
import os
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime

# ────────────────────────────────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────────────────────────────────

API_URL    = os.getenv("NEOBOT_API",    "http://localhost:8000")
TENANT_ID  = int(os.getenv("NEOBOT_TENANT", "1"))
TOKEN_FILE = os.path.expanduser("~/.neobot_token")

AGENT_TYPES = {
    "rdv":          "Prise de rendez-vous",
    "vente":        "Vente / Commercial",
    "support":      "Support client",
    "faq":          "FAQ / Infos",
    "libre":        "Usage libre",
    "qualification":"Qualification leads",
}

DELAYS = {
    "immediate": "Immédiat (0-1s)  — très rapide, aspect robot",
    "natural":   "Naturel  (1-3s)  — recommandé, semble humain",
    "human":     "Humain   (3-6s)  — comme si quelqu'un tape",
    "slow":      "Lent     (5-10s) — pour les messages longs",
}

# ANSI colors
G = "\033[92m"   # green
Y = "\033[93m"   # yellow
R = "\033[91m"   # red
B = "\033[94m"   # blue
C = "\033[96m"   # cyan
M = "\033[95m"   # magenta
W = "\033[97m"   # white bold
DIM = "\033[2m"
RST = "\033[0m"
BOLD = "\033[1m"

def ok(msg):  print(f"{G}✓{RST} {msg}")
def err(msg): print(f"{R}✗{RST} {msg}", file=sys.stderr)
def warn(msg):print(f"{Y}!{RST} {msg}")
def info(msg):print(f"{B}›{RST} {msg}")
def sep():    print(f"{DIM}{'─'*60}{RST}")

# ────────────────────────────────────────────────────────────────────────────
# HTTP helpers
# ────────────────────────────────────────────────────────────────────────────

def _token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    return None

def _save_token(tok):
    with open(TOKEN_FILE, "w") as f:
        f.write(tok)
    os.chmod(TOKEN_FILE, 0o600)

def _req(method, path, data=None, auth=True, timeout=15):
    url = f"{API_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if auth:
        tok = _token()
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.time() - t0
            return json.loads(resp.read()), elapsed
    except urllib.error.HTTPError as e:
        body_err = e.read().decode(errors="replace")
        try:
            detail = json.loads(body_err).get("detail", body_err)
        except Exception:
            detail = body_err
        raise RuntimeError(f"HTTP {e.code}: {detail}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Connexion refusée — le backend tourne ? ({e.reason})")

def GET(path, **kw):    return _req("GET",    path, **kw)
def POST(path, d, **kw):return _req("POST",   path, data=d, **kw)
def PUT(path,  d, **kw):return _req("PUT",    path, data=d, **kw)
def DELETE(path, **kw): return _req("DELETE", path, **kw)

# ────────────────────────────────────────────────────────────────────────────
# BANNER
# ────────────────────────────────────────────────────────────────────────────

def banner():
    print(f"""
{C}{BOLD}╔═══════════════════════════════════════╗
║   NEOBOT CLI  —  L'IA à votre service ║
╚═══════════════════════════════════════╝{RST}
  API  : {W}{API_URL}{RST}
  Tenant : {W}{TENANT_ID}{RST}
""")

# ────────────────────────────────────────────────────────────────────────────
# COMMANDES
# ────────────────────────────────────────────────────────────────────────────

# ── 1. STATUS ────────────────────────────────────────────────────────────────

def cmd_status(_):
    """Vérifie que le backend et WhatsApp sont up."""
    print(f"\n{BOLD}=== Santé du système ==={RST}\n")
    
    # Backend
    try:
        data, ms = GET("/health", auth=False)
        ok(f"Backend  {G}UP{RST}  ({ms*1000:.0f}ms)")
    except Exception as e:
        err(f"Backend  DOWN — {e}")
    
    # Base de données
    try:
        data, _ = GET("/api/health", auth=False)
        if data.get("database") == "connected":
            ok(f"Database {G}OK{RST}")
        else:
            warn(f"Database {Y}dégradé{RST}")
    except Exception as e:
        err(f"Database DOWN — {e}")
    
    # WhatsApp service
    try:
        data, ms = GET(f"/api/tenants/{TENANT_ID}/whatsapp/status", auth=False)
        connected = data.get("connected", data.get("is_connected", False))
        phone     = data.get("phone", data.get("whatsapp_phone", "?"))
        if connected:
            ok(f"WhatsApp {G}CONNECTÉ{RST}  numéro={phone}  ({ms*1000:.0f}ms)")
        else:
            warn(f"WhatsApp {Y}DÉCONNECTÉ{RST}  ({ms*1000:.0f}ms)")
    except Exception as e:
        warn(f"WhatsApp {Y}service inaccessible{RST} — {e}")
    
    # Tenant info
    try:
        data, _ = GET(f"/api/tenants/{TENANT_ID}")
        info(f"Tenant «{data.get('name','?')}»  plan={data.get('plan','?')}  "
             f"msgs={data.get('messages_used','?')}/{data.get('messages_limit','?')}")
    except Exception as e:
        warn(f"Tenant info non disponible — {e}")
    print()

# ── 2. LOGIN ─────────────────────────────────────────────────────────────────

def cmd_login(args):
    """Se connecter et sauvegarder le token."""
    print(f"\n{BOLD}=== Connexion ==={RST}\n")
    email    = args.email    or input(f"{C}Email    : {RST}")
    password = args.password or input(f"{C}Password : {RST}")
    try:
        data, _ = POST("/api/auth/login", {"email": email, "password": password}, auth=False)
        _save_token(data["access_token"])
        ok(f"Connecté en tant que {W}{email}{RST}")
        info(f"user_id={data['user_id']}  tenant_id={data['tenant_id']}")
        info(f"Token sauvegardé dans {TOKEN_FILE}")
    except Exception as e:
        err(f"Échec login : {e}")
    print()

# ── 3. LIST-AGENTS ───────────────────────────────────────────────────────────

def cmd_list_agents(_):
    """Lister tous les agents du tenant."""
    print(f"\n{BOLD}=== Agents actifs ==={RST}\n")
    try:
        data, _ = GET(f"/api/tenants/{TENANT_ID}/agents")
        agents = data if isinstance(data, list) else data.get("agents", [])
        if not agents:
            warn("Aucun agent trouvé. Crée-en un avec : python neobot.py create")
            return
        for a in agents:
            active = f"{G}ACTIF{RST}" if a.get("is_active") else f"{DIM}inactif{RST}"
            delay  = a.get("response_delay", "natural")
            print(f"  [{W}{a['id']}{RST}] {BOLD}{a['name']}{RST}")
            print(f"       type={C}{a.get('agent_type','?')}{RST}  delay={Y}{delay}{RST}  statut={active}")
            print(f"       {DIM}créé {a.get('created_at','')[:10]}{RST}")
            sep()
    except Exception as e:
        err(f"Erreur : {e}")
    print()

# ── 4. CREATE-AGENT ──────────────────────────────────────────────────────────

def cmd_create(args):
    """Créer un nouvel agent."""
    print(f"\n{BOLD}=== Créer un agent ==={RST}\n")
    
    # Type
    if args.type:
        atype = args.type.lower()
    else:
        print("Types disponibles :")
        for k, v in AGENT_TYPES.items():
            print(f"  {C}{k:<15}{RST} {v}")
        atype = input(f"\n{C}Type : {RST}").strip().lower()
    
    if atype not in AGENT_TYPES:
        err(f"Type invalide. Choix : {', '.join(AGENT_TYPES)}")
        return
    
    name  = args.name  or input(f"{C}Nom de l'agent : {RST}")
    delay = args.delay or "natural"
    
    if delay not in DELAYS:
        warn(f"Délai invalide, utilisation de 'natural'")
        delay = "natural"
    
    payload = {
        "name":            name,
        "agent_type":      atype.upper(),
        "response_delay":  delay,
        "typing_indicator": True,
        "activate":        True,
    }
    if args.prompt:
        payload["custom_prompt"] = args.prompt
    
    try:
        data, _ = POST(f"/api/tenants/{TENANT_ID}/agents", payload)
        agent_id = data.get("id") or data.get("agent_id")
        ok(f"Agent créé ! ID={W}{agent_id}{RST}  nom={W}{name}{RST}  type={C}{atype}{RST}")
        info(f"Test immédiat : {Y}python neobot.py chat --id {agent_id}{RST}")
    except Exception as e:
        err(f"Erreur création : {e}")
    print()

# ── 5. UPDATE-AGENT ──────────────────────────────────────────────────────────

def cmd_update(args):
    """Modifier un agent existant."""
    print(f"\n{BOLD}=== Modifier l'agent #{args.id} ==={RST}\n")
    
    payload = {}
    if args.name:   payload["name"]            = args.name
    if args.delay:  payload["response_delay"]  = args.delay
    if args.prompt: payload["custom_prompt"]   = args.prompt
    if args.tone:   payload["tone"]            = args.tone
    if not payload:
        warn("Rien à modifier. Utilise --name, --delay, --prompt, --tone")
        return
    
    try:
        data, _ = PUT(f"/api/tenants/{TENANT_ID}/agents/{args.id}", payload)
        ok(f"Agent #{args.id} mis à jour")
        for k, v in payload.items():
            info(f"  {k} = {W}{v}{RST}")
    except Exception as e:
        err(f"Erreur : {e}")
    print()

# ── 6. DELETE-AGENT ──────────────────────────────────────────────────────────

def cmd_delete(args):
    """Supprimer un agent."""
    print(f"\n{BOLD}=== Supprimer l'agent #{args.id} ==={RST}\n")
    confirm = input(f"{R}Confirmer la suppression ? (oui/non) : {RST}")
    if confirm.lower() not in ("oui", "o", "yes", "y"):
        warn("Annulé.")
        return
    try:
        DELETE(f"/api/tenants/{TENANT_ID}/agents/{args.id}")
        ok(f"Agent #{args.id} supprimé.")
    except Exception as e:
        err(f"Erreur : {e}")
    print()

# ── 7. SHOW-AGENT ────────────────────────────────────────────────────────────

def cmd_show(args):
    """Afficher la config complète d'un agent."""
    print(f"\n{BOLD}=== Agent #{args.id} ==={RST}\n")
    try:
        data, _ = GET(f"/api/tenants/{TENANT_ID}/agents/{args.id}")
        keys_order = ["id","name","agent_type","response_delay","typing_indicator",
                      "is_active","tone","language","emoji_enabled","max_response_length",
                      "availability_start","availability_end","created_at"]
        for k in keys_order:
            if k in data:
                val = data[k]
                if isinstance(val, bool):
                    val = f"{G}Oui{RST}" if val else f"{R}Non{RST}"
                print(f"  {DIM}{k:<25}{RST} {W}{val}{RST}")
        
        # Prompt
        if data.get("system_prompt"):
            print(f"\n{BOLD}Prompt système (extrait) :{RST}")
            print(f"  {DIM}{data['system_prompt'][:300]}...{RST}")
        if data.get("custom_prompt"):
            print(f"\n{BOLD}Prompt personnalisé :{RST}")
            print(f"  {C}{data['custom_prompt']}{RST}")
    except Exception as e:
        err(f"Erreur : {e}")
    print()

# ── 8. ADD-KNOWLEDGE ─────────────────────────────────────────────────────────

def cmd_knowledge(args):
    """Ajouter une source de connaissance à un agent."""
    print(f"\n{BOLD}=== Ajouter une connaissance → Agent #{args.id} ==={RST}\n")
    
    ktype = args.ktype or "text"
    
    if ktype == "text":
        content = args.content or input(f"{C}Contenu texte (FAQ, infos...) :\n{RST}")
        payload = {
            "source_type": "text",
            "name":         args.kname or "Connaissance manuelle",
            "content_text": content,
        }
    elif ktype == "url":
        url_src = args.url or input(f"{C}URL à indexer : {RST}")
        payload = {
            "source_type": "url",
            "name":         args.kname or url_src,
            "source_url":   url_src,
        }
    else:
        err(f"Type de source '{ktype}' non supporté ici. Utilise text ou url.")
        return
    
    try:
        data, _ = POST(f"/api/tenants/{TENANT_ID}/agents/{args.id}/knowledge", payload)
        ok(f"Connaissance ajoutée (ID={data.get('id','?')})")
    except Exception as e:
        err(f"Erreur : {e}")
    print()

# ── 9. ACTIVATE / DEACTIVATE ─────────────────────────────────────────────────

def cmd_activate(args):
    """Activer un agent."""
    try:
        PUT(f"/api/tenants/{TENANT_ID}/agents/{args.id}", {"is_active": True})
        ok(f"Agent #{args.id} {G}ACTIVÉ{RST}")
    except Exception as e:
        err(f"Erreur : {e}")

def cmd_deactivate(args):
    """Désactiver un agent."""
    try:
        PUT(f"/api/tenants/{TENANT_ID}/agents/{args.id}", {"is_active": False})
        ok(f"Agent #{args.id} {Y}DÉSACTIVÉ{RST}")
    except Exception as e:
        err(f"Erreur : {e}")

# ── 10. SEND (test rapide) ───────────────────────────────────────────────────

def cmd_send(args):
    """Envoi unique d'un message → réponse immédiate."""
    msg = args.message
    phone = args.phone or "+237600000001"
    print(f"\n{BOLD}=== Test rapide ==={RST}\n")
    info(f"Message : {W}{msg}{RST}")
    info(f"Phone   : {W}{phone}{RST}\n")
    _do_chat(msg, phone, args.agent_id)
    print()

# ── 11. CHAT (mode interactif) ───────────────────────────────────────────────

def cmd_chat(args):
    """Mode conversation interactive avec le bot."""
    phone    = args.phone    or "+237600000001"
    agent_id = args.id

    print(f"""
{C}{BOLD}╔════════════════════════════════════════╗
║   MODE CHAT — WhatsApp Simulator       ║
╠════════════════════════════════════════╣
║  phone   : {phone:<28}║
║  agent   : {str(agent_id) + ' (auto si vide)':<28}║
║  Ctrl+C  pour quitter                  ║
╚════════════════════════════════════════╝{RST}
{DIM}Tape ton message et appuie sur Entrée.{RST}
{DIM}Commandes spéciales : /clear /timing /quit{RST}
""")

    show_timing = True
    
    try:
        while True:
            try:
                user_input = input(f"{W}Toi{RST}  › ").strip()
            except EOFError:
                break
            
            if not user_input:
                continue
            if user_input == "/quit":
                break
            if user_input == "/clear":
                os.system("clear")
                continue
            if user_input == "/timing":
                show_timing = not show_timing
                info(f"Timing {'affiché' if show_timing else 'masqué'}")
                continue
            if user_input.startswith("/help"):
                print(f"  {C}/quit{RST}    — quitter")
                print(f"  {C}/clear{RST}   — effacer l'écran")
                print(f"  {C}/timing{RST}  — afficher/masquer le temps de réponse")
                continue
            
            _do_chat(user_input, phone, agent_id, show_timing=show_timing)
            
    except KeyboardInterrupt:
        print(f"\n{DIM}Session terminée.{RST}")
    print()

def _do_chat(message, phone, agent_id=None, show_timing=True):
    """Envoie un message et affiche la réponse formatée."""
    payload = {
        "from":      phone,
        "message":   message,
        "tenant_id": TENANT_ID,
    }
    if agent_id:
        payload["agent_id"] = agent_id
    
    try:
        t0 = time.time()
        data, elapsed = POST("/api/whatsapp/message", payload)
        bot_reply = (data.get("response")
                  or data.get("reply")
                  or data.get("message")
                  or str(data))
        
        timing_str = f"  {DIM}({elapsed*1000:.0f}ms){RST}" if show_timing else ""
        print(f"{G}Bot{RST}  › {C}{bot_reply}{RST}{timing_str}")
        
        # Score qualité du timing
        if show_timing:
            if elapsed > 5:
                warn(f"Réponse lente ({elapsed:.1f}s) — vérifie ta connexion DeepSeek")
        
        return bot_reply
    except Exception as e:
        err(f"Erreur envoi : {e}")
        return None

# ── 12. WHATSAPP QR ──────────────────────────────────────────────────────────

def cmd_qr(_):
    """Afficher le QR code pour connecter WhatsApp."""
    print(f"\n{BOLD}=== Connexion WhatsApp ==={RST}\n")
    try:
        data, _ = GET(f"/api/tenants/{TENANT_ID}/whatsapp/qr")
        status  = data.get("status","?")
        
        if status == "connected":
            ok(f"WhatsApp déjà connecté ! Numéro : {W}{data.get('phone','?')}{RST}")
        elif status == "awaiting_scan":
            info("Ouvre WhatsApp → Appareils connectés → Scanner un QR code")
            info(f"QR disponible sur : {Y}http://localhost:3001/qr/{TENANT_ID}{RST}")
            if data.get("qr_code"):
                ok("QR Code généré. Rendez-vous sur l'URL ci-dessus pour le scanner.")
        else:
            warn(f"Statut : {status}")
            if data.get("message"):
                info(data["message"])
    except Exception as e:
        err(f"Erreur : {e}")
    print()

def cmd_whatsapp_status(_):
    """Voir le statut de la connexion WhatsApp."""
    print(f"\n{BOLD}=== Statut WhatsApp ==={RST}\n")
    try:
        data, _ = GET(f"/api/tenants/{TENANT_ID}/whatsapp/status")
        connected = data.get("connected", data.get("is_connected", False))
        phone     = data.get("phone", data.get("whatsapp_phone", "Non connecté"))
        
        if connected:
            ok(f"Connecté — numéro {W}{phone}{RST}")
        else:
            warn(f"Non connecté")
            info("Lance : python neobot.py qr")
    except Exception as e:
        err(f"Erreur : {e}")
    print()

# ── 13. WATCH (surveillance live) ────────────────────────────────────────────

def cmd_watch(args):
    """Surveiller les messages en temps réel (polling)."""
    interval = args.interval or 3
    print(f"""
{C}{BOLD}╔════════════════════════════════════════╗
║   WATCH — Messages en temps réel       ║
╠════════════════════════════════════════╣
║  refresh : toutes les {interval}s                  ║
║  Ctrl+C  pour arrêter                  ║
╚════════════════════════════════════════╝{RST}
""")
    seen_ids = set()
    
    try:
        while True:
            try:
                data, _ = GET(f"/api/conversations/{TENANT_ID}")
                convs = data.get("conversations", [])
                
                for conv in convs:
                    cid = conv["id"]
                    try:
                        msgs_data, _ = GET(f"/api/messages/{cid}")
                        for m in msgs_data.get("messages", []):
                            mid = m["id"]
                            if mid not in seen_ids:
                                seen_ids.add(mid)
                                ts    = m["created_at"][11:19]
                                who   = f"{G}BOT{RST} " if m["is_ai"] else f"{Y}USR{RST}"
                                arrow = "→" if m["direction"] == "outgoing" else "←"
                                phone = conv["customer_phone"][-8:]
                                print(f"  [{ts}] {who} {arrow} [{phone}]  {m['content'][:100]}")
                    except Exception:
                        pass
                
                print(f"  {DIM}· {datetime.now().strftime('%H:%M:%S')} — {len(convs)} conversations actives{RST}", end="\r")
                time.sleep(interval)
                
            except Exception as e:
                err(f"Erreur polling : {e}")
                time.sleep(interval)
                
    except KeyboardInterrupt:
        print(f"\n{DIM}Watch arrêté.{RST}")
    print()

# ── 14. GENERATE PROMPT ──────────────────────────────────────────────────────

def cmd_gen_prompt(args):
    """Générer un prompt IA pour un agent."""
    print(f"\n{BOLD}=== Générer un prompt pour l'agent #{args.id} ==={RST}\n")
    
    company  = args.company  or input(f"{C}Nom de l'entreprise : {RST}")
    products = args.products or input(f"{C}Produits/Services   : {RST}")
    btype    = args.btype    or input(f"{C}Type d'entreprise   : {RST}")
    
    payload = {
        "company_name":       company,
        "products_services":  products,
        "business_type":      btype,
        "tone":               args.tone or "Friendly, Professional",
        "target_audience":    args.audience or "Clients généraux",
    }
    
    try:
        data, elapsed = POST(f"/api/tenants/{TENANT_ID}/agents/{args.id}/generate-prompt", payload)
        prompt = data.get("prompt") or data.get("generated_prompt","")
        score  = data.get("score","?")
        
        ok(f"Prompt généré en {elapsed*1000:.0f}ms  (score={score})")
        print(f"\n{BOLD}─── Prompt ───{RST}")
        print(f"{C}{prompt}{RST}")
        
        if input(f"\n{Y}Appliquer ce prompt à l'agent #{args.id} ? (oui/non) : {RST}").lower() in ("oui","o","y"):
            PUT(f"/api/tenants/{TENANT_ID}/agents/{args.id}", {"custom_prompt": prompt})
            ok("Prompt appliqué !")
    except Exception as e:
        err(f"Erreur : {e}")
    print()

# ── 15. BENCHMARK ─────────────────────────────────────────────────────────────

def cmd_bench(args):
    """Benchmark : N messages → statistiques de temps de réponse."""
    n     = args.n or 5
    phone = "+237600000099"
    msgs  = [
        "Bonjour, vous êtes disponible ?",
        "Quels sont vos tarifs ?",
        "Comment commander ?",
        "C'est livré en combien de temps ?",
        "Avez-vous des promotions ?",
    ]
    
    print(f"\n{BOLD}=== Benchmark — {n} messages ==={RST}\n")
    
    times = []
    for i in range(n):
        msg = msgs[i % len(msgs)]
        print(f"  [{i+1}/{n}] {DIM}{msg[:45]}{RST}", end="  ", flush=True)
        payload = {"from": phone, "message": msg, "tenant_id": TENANT_ID}
        try:
            t0 = time.time()
            POST("/api/whatsapp/message", payload)
            elapsed = time.time() - t0
            times.append(elapsed)
            color = G if elapsed < 3 else (Y if elapsed < 6 else R)
            print(f"{color}{elapsed*1000:.0f}ms{RST}")
        except Exception as e:
            print(f"{R}ERREUR{RST}")
        time.sleep(0.5)
    
    if times:
        sep()
        ok(f"Moyen  : {sum(times)/len(times)*1000:.0f}ms")
        ok(f"Min    : {min(times)*1000:.0f}ms")
        ok(f"Max    : {max(times)*1000:.0f}ms")
        if max(times) > 6:
            warn("Réponses lentes détectées → vérifie la clé DeepSeek ou la connexion internet")
    print()

# ── 16. HELP ─────────────────────────────────────────────────────────────────

def cmd_help(_):
    """Affiche l'aide complète."""
    print(f"""
{C}{BOLD}NEOBOT CLI — Toutes les commandes{RST}

{BOLD}SYSTÈME{RST}
  {G}status{RST}                       Vérifie backend + WhatsApp + DB
  {G}login{RST}  [--email] [--password] Se connecter (requis 1 fois)
  {G}qr{RST}                           Affiche/génère le QR WhatsApp

{BOLD}AGENTS{RST}
  {G}list{RST}                         Lister tous tes agents
  {G}show{RST}   --id N                Voir la config complète d'un agent
  {G}create{RST} [--type] [--name] [--delay] [--prompt]
                               Créer un agent
  {G}update{RST} --id N [--name] [--delay] [--prompt] [--tone]
                               Modifier un agent
  {G}delete{RST} --id N                Supprimer un agent
  {G}on{RST}     --id N                Activer un agent
  {G}off{RST}    --id N                Désactiver un agent

{BOLD}TESTER{RST}
  {G}send{RST}   --message "..." [--phone X] [--agent-id N]
                               Test rapide (1 message)
  {G}chat{RST}   [--id N] [--phone X] Mode chat interactif (Ctrl+C pour quitter)
  {G}watch{RST}  [--interval N]        Surveiller les messages en live (polling)
  {G}bench{RST}  [--n N]               Benchmark de performance (N messages)

{BOLD}CONTENU{RST}
  {G}knowledge{RST} --id N [--ktype text|url] [--content "..."] [--url "..."]
                               Ajouter une connaissance à un agent
  {G}gen-prompt{RST} --id N [--company] [--products] [--btype]
                               Générer un prompt IA et l'appliquer

{BOLD}OPTIONS GLOBALES{RST}
  {DIM}NEOBOT_API=http://localhost:8000  (variable d'env)
  NEOBOT_TENANT=1                  (variable d'env){RST}

{BOLD}EXEMPLES RAPIDES{RST}
  {Y}python neobot.py status{RST}
  {Y}python neobot.py login --email admin@neobot.app --password MonPass{RST}
  {Y}python neobot.py create --type rdv --name "Bot Médecin" --delay human{RST}
  {Y}python neobot.py chat --id 1{RST}
  {Y}python neobot.py send --message "Bonjour" --agent-id 1{RST}
  {Y}python neobot.py watch{RST}
  {Y}python neobot.py bench --n 10{RST}
""")

# ────────────────────────────────────────────────────────────────────────────
# MAIN / ROUTER
# ────────────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        prog="neobot",
        description="NéoBot CLI — pilotez votre bot WhatsApp IA",
        add_help=False,
    )
    p.add_argument("command", nargs="?", default="help")
    p.add_argument("--id",        type=int,   help="ID de l'agent")
    p.add_argument("--type",      type=str,   help="Type d'agent : rdv|vente|support|faq|libre|qualification")
    p.add_argument("--name",      type=str,   help="Nom de l'agent")
    p.add_argument("--delay",     type=str,   help="Délai : immediate|natural|human|slow")
    p.add_argument("--prompt",    type=str,   help="Prompt personnalisé")
    p.add_argument("--tone",      type=str,   help="Ton : Friendly, Professional, etc.")
    p.add_argument("--message",   type=str,   help="Message à envoyer")
    p.add_argument("--phone",     type=str,   help="Numéro WhatsApp simulé")
    p.add_argument("--agent-id",  type=int,   dest="agent_id", help="Cibler un agent spécifique")
    p.add_argument("--interval",  type=int,   help="Intervalle polling (secondes)")
    p.add_argument("--n",         type=int,   help="Nombre d'itérations (bench)")
    p.add_argument("--ktype",     type=str,   help="Type de connaissance : text|url")
    p.add_argument("--kname",     type=str,   help="Nom de la source")
    p.add_argument("--content",   type=str,   help="Contenu texte")
    p.add_argument("--url",       type=str,   help="URL source")
    p.add_argument("--company",   type=str,   help="Nom entreprise (gen-prompt)")
    p.add_argument("--products",  type=str,   help="Produits/services (gen-prompt)")
    p.add_argument("--btype",     type=str,   help="Type entreprise (gen-prompt)")
    p.add_argument("--audience",  type=str,   help="Audience cible (gen-prompt)")
    p.add_argument("--email",     type=str,   help="Email (login)")
    p.add_argument("--password",  type=str,   help="Mot de passe (login)")

    args = p.parse_args()

    COMMANDS = {
        "status":     cmd_status,
        "login":      cmd_login,
        "list":       cmd_list_agents,
        "show":       cmd_show,
        "create":     cmd_create,
        "update":     cmd_update,
        "delete":     cmd_delete,
        "on":         cmd_activate,
        "off":        cmd_deactivate,
        "send":       cmd_send,
        "chat":       cmd_chat,
        "watch":      cmd_watch,
        "qr":         cmd_qr,
        "whatsapp":   cmd_whatsapp_status,
        "knowledge":  cmd_knowledge,
        "gen-prompt": cmd_gen_prompt,
        "bench":      cmd_bench,
        "help":       cmd_help,
        "-h":         cmd_help,
        "--help":     cmd_help,
    }

    banner()

    cmd = args.command.lower()
    if cmd in COMMANDS:
        COMMANDS[cmd](args)
    else:
        err(f"Commande inconnue : '{cmd}'")
        cmd_help(None)

if __name__ == "__main__":
    main()
