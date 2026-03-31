"""
Router Sentry webhook — analyse automatique des erreurs avec Claude Haiku,
création GitHub Issues, email Brevo.

Sécurité : signature HMAC-SHA256 obligatoire (header sentry-hook-signature).
Toute requête non signée est rejetée avec 401.
"""
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import httpx
import sentry_sdk
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SentryAlert
from ..services import claude_service
from ..services.email_service import send_internal_alert, SENDER_EMAIL

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sentry", tags=["sentry"])

SENTRY_WEBHOOK_SECRET = os.getenv("SENTRY_WEBHOOK_SECRET", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

GITHUB_REPOS = {
    "backend":   os.getenv("GITHUB_REPO_BACKEND", ""),
    "frontend":  os.getenv("GITHUB_REPO_FRONTEND", ""),
    "whatsapp":  os.getenv("GITHUB_REPO_WHATSAPP", ""),
}

# Anti-spam : 1h minimum entre deux analyses Claude pour la même erreur
ALERT_COOLDOWN_MINUTES = 60


# ─── Vérification signature ───────────────────────────────────────────────────

def _verify_sentry_signature(raw_body: bytes, signature_header: str) -> bool:
    """
    Vérifie la signature HMAC-SHA256 envoyée par Sentry.
    Header : sentry-hook-signature
    """
    if not SENTRY_WEBHOOK_SECRET:
        logger.warning("SENTRY_WEBHOOK_SECRET non défini — toutes les requêtes rejetées")
        return False
    if not signature_header:
        return False
    try:
        expected = hmac.new(
            SENTRY_WEBHOOK_SECRET.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header)
    except Exception:
        return False


# ─── Extraction du payload Sentry ────────────────────────────────────────────

def _extract_sentry_data(payload: dict) -> dict:
    """
    Normalise le payload Sentry en un dict standard exploitable.
    Sentry peut envoyer plusieurs formats selon l'événement.
    """
    action = payload.get("action", "")
    data   = payload.get("data", {})
    issue  = data.get("issue", {})

    error_id = str(issue.get("id", "")) or payload.get("id", "")
    title    = issue.get("title", payload.get("message", "Erreur inconnue"))

    # Métadonnées
    metadata = issue.get("metadata", {})
    error_message = (
        metadata.get("value")
        or issue.get("culprit", "")
        or title
    )

    # Stack trace — Sentry envoie soit dans lastEvent soit dans la structure principale
    last_event = issue.get("lastEvent", {})
    entries = last_event.get("entries", [])
    stack_trace = ""
    for entry in entries:
        if entry.get("type") == "exception":
            values = entry.get("data", {}).get("values", [])
            for val in values:
                st = val.get("stacktrace", {}).get("frames", [])
                lines = []
                for frame in st[-10:]:  # 10 derniers frames suffisent
                    lines.append(
                        f"  File {frame.get('filename','?')}, line {frame.get('lineno','?')}, in {frame.get('function','?')}"
                    )
                    if frame.get("context_line"):
                        lines.append(f"    {frame['context_line'].strip()}")
                stack_trace = "\n".join(lines)
                break
        if stack_trace:
            break

    if not stack_trace:
        stack_trace = issue.get("culprit", "Stack trace non disponible")

    # Déterminer le service selon le projet Sentry
    project = issue.get("project", {}).get("slug", "") or payload.get("project", "")
    if "frontend" in project or "next" in project:
        service = "frontend"
    elif "whatsapp" in project or "baileys" in project:
        service = "whatsapp"
    else:
        service = "backend"

    return {
        "error_id":       error_id,
        "title":          title,
        "error_message":  error_message,
        "stack_trace":    stack_trace,
        "service":        service,
        "occurrences":    issue.get("count", 1),
        "first_seen":     issue.get("firstSeen", ""),
        "last_seen":      issue.get("lastSeen", ""),
        "sentry_url":     issue.get("permalink", ""),
        "level":          issue.get("level", "error"),
        "action":         action,
    }


# ─── GitHub Issue ─────────────────────────────────────────────────────────────

async def _create_github_issue(
    service: str,
    analysis: dict,
    error_data: dict,
) -> Optional[str]:
    """
    Crée une GitHub Issue si necessite_intervention = True.
    Retourne l'URL de l'Issue créée, ou None si échec.
    """
    repo = GITHUB_REPOS.get(service, GITHUB_REPOS.get("backend", ""))
    if not repo or not GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN ou GITHUB_REPO_%s non défini", service.upper())
        return None

    severity_upper = analysis.get("severite", "haute").upper()
    severity_emoji = {"CRITIQUE": "🔴", "HAUTE": "🟠", "MOYENNE": "🟡"}.get(severity_upper, "🟡")
    titre = analysis.get("titre_issue", error_data["title"])[:50]

    fichiers_md = "\n".join(f"- `{f}`" for f in analysis.get("fichiers_concernes", []))
    prompt_copilot = analysis.get("prompt_agent") or ""
    prompt_section = (
        f"\n## Prompt Copilot — Copie-colle directement\n```\n{prompt_copilot}\n```"
        if prompt_copilot
        else ""
    )

    body = f"""## Erreur détectée par Sentry

- **Service :** {service}
- **Occurrences :** {error_data['occurrences']} fois
- **Première vue :** {error_data['first_seen']}
- **Dernière vue :** {error_data['last_seen']}

## Cause probable
{analysis.get('cause_probable', 'N/A')}

## Impact
{analysis.get('impact', 'N/A')}

## Solution proposée
{analysis.get('solution', 'N/A')}

## Fichiers à modifier
{fichiers_md or '(non identifiés)'}
{prompt_section}

## Liens
- Sentry : {error_data.get('sentry_url', 'N/A')}

---
*Créée automatiquement par NeoBot Sentry Monitor — {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC*
"""

    issue_payload = {
        "title": f"[{severity_upper}] {titre}",
        "body": body,
        "labels": analysis.get("labels", ["bug"]),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"https://api.github.com/repos/{repo}/issues",
                json=issue_payload,
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            resp.raise_for_status()
            issue_url = resp.json().get("html_url", "")
            logger.info("GitHub Issue créée: %s", issue_url)
            return issue_url
    except Exception as exc:
        logger.error("Échec création GitHub Issue: %s", exc)
        sentry_sdk.capture_exception(exc)
        return None


async def _update_github_issue_count(issue_url: str, new_count: int) -> None:
    """Met à jour le titre de l'Issue avec le nouveau nombre d'occurrences."""
    if not GITHUB_TOKEN or not issue_url:
        return
    # Extraire owner/repo/issue_number depuis l'URL
    try:
        parts = issue_url.rstrip("/").split("/")
        owner, repo_name, issue_number = parts[-4], parts[-3], parts[-1]
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_number}",
                headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"},
            )
            if resp.status_code == 200:
                current = resp.json()
                await client.patch(
                    f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_number}",
                    json={"body": current["body"] + f"\n\n> 🔄 Mise à jour : **{new_count} occurrences** — {datetime.utcnow().strftime('%d/%m %H:%M')}"},
                    headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"},
                )
    except Exception as exc:
        logger.warning("Mise à jour Issue GitHub échouée: %s", exc)


# ─── Email alerte Sentry ──────────────────────────────────────────────────────

async def _send_sentry_email(
    analysis: dict,
    error_data: dict,
    issue_url: Optional[str],
) -> None:
    severity = analysis.get("severite", "haute").upper()
    icon = {"CRITIQUE": "🔴", "HAUTE": "🟠", "MOYENNE": "🟡"}.get(severity, "🟡")

    subject = f"{icon} [{severity}] {analysis['titre_issue']} ({error_data['occurrences']}x)"

    issue_link = (
        f'<p><a href="{issue_url}" style="color:#FF4D00;font-weight:bold;">Voir la GitHub Issue →</a></p>'
        if issue_url else ""
    )
    sentry_link = (
        f'<p><a href="{error_data["sentry_url"]}" style="color:#FF7A40;">Voir dans Sentry →</a></p>'
        if error_data.get("sentry_url") else ""
    )

    body = f"""
<h2 style="color:#FF4D00;">{icon} Erreur {severity} — {error_data['service']}</h2>
<p style="color:#aaa;">{error_data['occurrences']} occurrence(s) • Dernière : {error_data['last_seen']}</p>
<hr style="border-color:#333;">
<h3>Cause</h3>
<p>{analysis.get('cause_probable','N/A')}</p>
<h3>Impact</h3>
<p>{analysis.get('impact','N/A')}</p>
<hr style="border-color:#333;">
{issue_link}
{sentry_link}
<p style="color:#555;font-size:11px;">Le détail complet + prompt Copilot est dans la GitHub Issue.</p>
"""
    await send_internal_alert(subject=subject, body=body)


# ─── Endpoint webhook ─────────────────────────────────────────────────────────

@router.post("/webhook", summary="Webhook Sentry — analyse automatique des erreurs")
async def sentry_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Reçoit les webhooks Sentry (issue.created, issue.escalating).
    - Vérifie la signature HMAC-SHA256
    - Traite uniquement les niveaux 'error' et 'fatal'
    - Anti-spam : 1 analyse Claude max par erreur par heure
    - Crée une GitHub Issue si necessite_intervention = True
    - Envoie un email résumé à neobot561@gmail.com
    """
    raw_body = await request.body()
    sig_header = request.headers.get("sentry-hook-signature", "")

    if not _verify_sentry_signature(raw_body, sig_header):
        logger.warning("Sentry webhook rejeté — signature invalide (IP: %s)", request.client.host)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature invalide")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload JSON invalide")

    err = _extract_sentry_data(payload)

    # Ignorer les warnings
    if err["level"] not in ("error", "fatal"):
        logger.debug("Sentry webhook ignoré — niveau: %s", err["level"])
        return {"status": "ignored", "reason": f"level={err['level']}"}

    if not err["error_id"]:
        logger.warning("Sentry webhook sans error_id — ignoré")
        return {"status": "ignored", "reason": "no error_id"}

    # ── Anti-spam : chercher en DB ────────────────────────────────────────────
    existing = db.query(SentryAlert).filter(SentryAlert.error_id == err["error_id"]).first()
    cooldown_limit = datetime.utcnow() - timedelta(minutes=ALERT_COOLDOWN_MINUTES)

    if existing:
        existing.occurrences_count += 1
        existing.last_seen_at = datetime.utcnow()
        db.commit()

        if existing.last_notified_at > cooldown_limit:
            # Dans la fenêtre d'1h — incrémenter sans re-créer
            if existing.issue_github_url:
                await _update_github_issue_count(existing.issue_github_url, existing.occurrences_count)
            logger.info("Sentry anti-spam — même erreur %s dans l'heure, occurrences: %d", err["error_id"][:12], existing.occurrences_count)
            return {"status": "deduplicated", "occurrences": existing.occurrences_count}

    # ── Analyse Claude ────────────────────────────────────────────────────────
    analysis = await claude_service.analyze_sentry_error(
        error_message=err["error_message"],
        stack_trace=err["stack_trace"],
        service=err["service"],
        occurrences_24h=err["occurrences"],
        first_seen=err["first_seen"],
        last_seen=err["last_seen"],
        sentry_url=err.get("sentry_url"),
    )

    if not analysis:
        logger.warning("Analyse Claude échouée pour %s — notification basique", err["error_id"][:12])
        analysis = {
            "severite": "haute",
            "cause_probable": err["error_message"],
            "impact": "Impact inconnu — analyse Claude indisponible",
            "solution": "Analyser manuellement dans Sentry.",
            "fichiers_concernes": [],
            "necessite_intervention": True,
            "prompt_agent": None,
            "titre_issue": err["title"][:50],
            "labels": ["bug", "haute", err["service"]],
        }

    # ── GitHub Issue ──────────────────────────────────────────────────────────
    issue_url = None
    if analysis.get("necessite_intervention"):
        issue_url = await _create_github_issue(err["service"], analysis, err)

    # ── Enregistrement en DB ──────────────────────────────────────────────────
    if existing:
        existing.last_notified_at = datetime.utcnow()
        existing.severity = analysis.get("severite")
        if issue_url:
            existing.issue_github_url = issue_url
    else:
        alert = SentryAlert(
            error_id=err["error_id"],
            title=analysis.get("titre_issue", err["title"])[:500],
            service=err["service"],
            severity=analysis.get("severite"),
            occurrences_count=err["occurrences"],
            last_notified_at=datetime.utcnow(),
            first_seen_at=datetime.fromisoformat(err["first_seen"].replace("Z", "+00:00")) if err.get("first_seen") else datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            sentry_url=err.get("sentry_url"),
            issue_github_url=issue_url,
        )
        db.add(alert)

    db.commit()

    # ── Email Brevo ───────────────────────────────────────────────────────────
    await _send_sentry_email(analysis, err, issue_url)

    logger.info(
        "Sentry webhook traité — service: %s, sévérité: %s, issue: %s",
        err["service"], analysis.get("severite"), issue_url or "aucune",
    )

    return {
        "status": "processed",
        "service": err["service"],
        "severity": analysis.get("severite"),
        "issue_url": issue_url,
    }
