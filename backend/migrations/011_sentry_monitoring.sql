-- Migration 011 — Sentry auto-analysis + API credits monitoring
-- À exécuter avec : psql -U postgres -d neobot_db -f migrations/011_sentry_monitoring.sql

-- ─── sentry_alerts ────────────────────────────────────────────────────────────
-- Anti-spam : 1 analyse Claude + 1 GitHub Issue par erreur unique par heure.
CREATE TABLE IF NOT EXISTS sentry_alerts (
    id                  SERIAL PRIMARY KEY,
    error_id            VARCHAR(255) NOT NULL UNIQUE,   -- ID unique Sentry (ex: issue_id)
    title               VARCHAR(500),
    service             VARCHAR(50),                    -- backend | frontend | whatsapp
    severity            VARCHAR(20),                    -- critique | haute | moyenne
    occurrences_count   INTEGER NOT NULL DEFAULT 1,
    status              VARCHAR(20) NOT NULL DEFAULT 'open',  -- open | resolved
    issue_github_url    TEXT,
    last_notified_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    first_seen_at       TIMESTAMP,
    last_seen_at        TIMESTAMP,
    sentry_url          TEXT,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_sentry_alerts_error_id ON sentry_alerts (error_id);
CREATE INDEX IF NOT EXISTS ix_sentry_alerts_status   ON sentry_alerts (status);
CREATE INDEX IF NOT EXISTS ix_sentry_alerts_service  ON sentry_alerts (service);

-- ─── api_credits ──────────────────────────────────────────────────────────────
-- Historique des soldes API pour le dashboard + graphique 30j + alertes.
CREATE TABLE IF NOT EXISTS api_credits (
    id              SERIAL PRIMARY KEY,
    provider        VARCHAR(30) NOT NULL,    -- deepseek | anthropic
    balance_usd     NUMERIC(12,4) NOT NULL,
    balance_tokens  BIGINT,                  -- tokens disponibles (si fourni par l'API)
    is_degraded     BOOLEAN NOT NULL DEFAULT FALSE,  -- mode dégradé actif
    checked_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_api_credits_provider   ON api_credits (provider);
CREATE INDEX IF NOT EXISTS ix_api_credits_checked_at ON api_credits (checked_at);
