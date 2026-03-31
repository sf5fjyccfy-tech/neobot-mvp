"""
Script one-shot : crée un agent LIBRE par défaut pour chaque tenant
qui n'en a pas encore. À exécuter une seule fois depuis la racine du projet.

Usage:
  source .venv/bin/activate
  python create_default_agents.py
"""
import sys
import os

# Ajouter le backend au path Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.database import SessionLocal
from app.models import Tenant, AgentTemplate, AgentType
from app.services.agent_service import AgentService

NEOBOT_TENANT_ID = 1  # NéoBot Admin — verrouillé côté AgentService, on skip explicitement


def main():
    db = SessionLocal()
    try:
        tenants_without_agent = (
            db.query(Tenant)
            .filter(Tenant.id != NEOBOT_TENANT_ID)
            .filter(
                ~db.query(AgentTemplate.id)
                .filter(AgentTemplate.tenant_id == Tenant.id)
                .exists()
            )
            .all()
        )

        if not tenants_without_agent:
            print("✅ Tous les tenants ont déjà au moins un agent.")
            return

        print(f"🔎 {len(tenants_without_agent)} tenant(s) sans agent :")
        for t in tenants_without_agent:
            print(f"  - id={t.id} | {t.name} | {t.email}")

        confirm = input("\nCréer un agent LIBRE 'Assistant IA' pour chacun ? [o/N] ").strip().lower()
        if confirm != 'o':
            print("Annulé.")
            return

        for t in tenants_without_agent:
            try:
                agent = AgentService.create_agent(
                    tenant_id=t.id,
                    name="Assistant IA",
                    agent_type=AgentType.LIBRE,
                    db=db,
                    activate=True,
                )
                print(f"  ✅ Agent '{agent.name}' créé (id={agent.id}) pour tenant {t.id} ({t.name})")
            except Exception as e:
                print(f"  ❌ Erreur pour tenant {t.id} ({t.name}): {e}")

        print("\nTerminé.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
