"""
Router admin — suivi des crédits API (DeepSeek + Anthropic).
Toutes les routes sont protégées par get_superadmin_user.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_superadmin_user
from ..models import ApiCredit, User
from ..services.monitoring_service import (
    check_and_store_credits,
    get_history,
    get_latest_balance,
    is_degraded_mode,
)

router = APIRouter(prefix="/api/admin/credits", tags=["admin", "monitoring"])


# ─── Schémas réponse ──────────────────────────────────────────────────────────

class ProviderStatus(BaseModel):
    provider: str
    balance_usd: Optional[float]
    balance_fcfa: Optional[int]
    daily_avg_usd: Optional[float]
    days_remaining: Optional[int]
    level: str        # green | orange | red | critical | unknown
    is_degraded: bool
    last_checked: Optional[str]


class HistoryPoint(BaseModel):
    date: str
    balance_usd: Optional[float]
    provider: str


class CreditsSummary(BaseModel):
    deepseek: ProviderStatus
    anthropic: ProviderStatus
    degraded_mode_active: bool


USD_TO_FCFA = 620.0


def _compute_level(provider: str, balance: Optional[float]) -> str:
    if balance is None or balance < 0:
        return "unknown"
    thresholds = {
        "deepseek":   [(5.0, "green"), (2.0, "orange"), (0.5, "red"), (0.0, "critical")],
        "anthropic":  [(2.0, "green"), (0.5, "orange"), (0.1, "red"), (0.0, "critical")],
    }
    for limit, label in thresholds.get(provider, []):
        if balance >= limit:
            return label
    return "critical"


def _build_provider_status(
    db: Session,
    provider: str,
) -> ProviderStatus:
    latest: Optional[ApiCredit] = get_latest_balance(db, provider)
    history = get_history(db, provider, days=7)

    # Moyenne journalière sur 7j
    daily_avg = None
    if len(history) >= 2:
        oldest = history[0]["balance_usd"]
        newest = history[-1]["balance_usd"]
        if oldest and newest and oldest > newest:
            daily_avg = round((oldest - newest) / max(len(history) - 1, 1), 4)

    balance = latest.balance_usd if latest else None
    days_remaining = None
    if balance and daily_avg and daily_avg > 0:
        days_remaining = int(balance / daily_avg)

    return ProviderStatus(
        provider=provider,
        balance_usd=round(balance, 4) if balance is not None else None,
        balance_fcfa=int(balance * USD_TO_FCFA) if balance and balance >= 0 else None,
        daily_avg_usd=daily_avg,
        days_remaining=days_remaining,
        level=_compute_level(provider, balance),
        is_degraded=latest.is_degraded if latest else False,
        last_checked=latest.checked_at.isoformat() if latest else None,
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("", response_model=CreditsSummary, summary="Soldes actuels DeepSeek + Anthropic")
def get_credits_summary(
    db: Session = Depends(get_db),
    _user: User = Depends(get_superadmin_user),
):
    """Retourne les soldes actuels + niveaux d'alerte."""
    return CreditsSummary(
        deepseek=_build_provider_status(db, "deepseek"),
        anthropic=_build_provider_status(db, "anthropic"),
        degraded_mode_active=is_degraded_mode(),
    )


@router.get("/history", response_model=List[HistoryPoint], summary="Historique 30j pour graphique")
def get_credits_history(
    days: int = 30,
    db: Session = Depends(get_db),
    _user: User = Depends(get_superadmin_user),
):
    """Retourne l'historique des balances (un point par mesure) pour alimenter le graphique."""
    if days > 90:
        raise HTTPException(status_code=400, detail="Maximum 90 jours")
    result = []
    for provider in ("deepseek", "anthropic"):
        for point in get_history(db, provider, days=days):
            result.append(HistoryPoint(
                date=point["date"],
                balance_usd=point.get("balance_usd"),
                provider=provider,
            ))
    return sorted(result, key=lambda x: x.date)


@router.post("/refresh", summary="Forcer une vérification immédiate des soldes")
async def force_refresh(
    db: Session = Depends(get_db),
    _user: User = Depends(get_superadmin_user),
):
    """
    Force une vérification immédiate des balances API (contourne le cron horaire).
    Utile après une recharge pour confirmer le nouveau solde.
    """
    result = await check_and_store_credits(db)
    return {"status": "refreshed", "results": result}
