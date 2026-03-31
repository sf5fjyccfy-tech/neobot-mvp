-- ============================================================
-- Migration 010: NeopPay — Système de paiement NeoBot
-- Tables: payment_links, payment_events, webhook_events
-- ============================================================

-- ─── PAYMENT LINKS ───────────────────────────────────────────────────────────
-- Lien de paiement unique à durée limitée (24h).
-- Généré à l'inscription ou manuellement par l'admin.
-- URL publique : /pay/{token}

CREATE TABLE IF NOT EXISTS payment_links (
    id              SERIAL PRIMARY KEY,
    token           VARCHAR(64) UNIQUE NOT NULL,   -- UUID hex, index pour lookup rapide
    tenant_id       INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plan            VARCHAR(50) NOT NULL,           -- BASIC | STANDARD | PRO
    amount          INTEGER NOT NULL,               -- Montant en centimes de devise
    currency        VARCHAR(10) NOT NULL DEFAULT 'NGN',
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending | paid | expired | cancelled
    expires_at      TIMESTAMP NOT NULL,
    paid_at         TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payment_links_token     ON payment_links(token);
CREATE INDEX IF NOT EXISTS idx_payment_links_tenant    ON payment_links(tenant_id);
CREATE INDEX IF NOT EXISTS idx_payment_links_status    ON payment_links(status, expires_at);

-- ─── PAYMENT EVENTS ──────────────────────────────────────────────────────────
-- Trace de chaque transaction, quel que soit le provider.
-- Source unique de vérité paiement. Jamais de données bancaires.

CREATE TABLE IF NOT EXISTS payment_events (
    id              SERIAL PRIMARY KEY,
    transaction_id  VARCHAR(255) UNIQUE NOT NULL,  -- ID provider (korapay ref ou campay txn)
    provider        VARCHAR(20) NOT NULL,           -- korapay | campay
    payment_link_id INTEGER REFERENCES payment_links(id) ON DELETE SET NULL,
    tenant_id       INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plan            VARCHAR(50) NOT NULL,
    amount          INTEGER NOT NULL,               -- Montant en centimes
    currency        VARCHAR(10) NOT NULL DEFAULT 'NGN',
    payment_method  VARCHAR(50),                    -- card | mobile_money | bank_transfer
    status          VARCHAR(30) NOT NULL DEFAULT 'initiated',
    -- initiated | pending | confirmed | failed | refunded | cancelled
    provider_raw_status VARCHAR(100),              -- Statut brut retourné par le provider
    failure_reason  TEXT,
    customer_email  VARCHAR(255),
    customer_phone  VARCHAR(50),
    payment_metadata JSONB,                          -- Données extra du provider (jamais de carte)
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payment_events_tenant      ON payment_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_payment_events_status      ON payment_events(status);
CREATE INDEX IF NOT EXISTS idx_payment_events_transaction ON payment_events(transaction_id);

-- ─── WEBHOOK EVENTS ──────────────────────────────────────────────────────────
-- Idempotence stricte : chaque webhook_id est traité une seule fois.
-- Retry automatique stocké ici si traitement échoue.

CREATE TABLE IF NOT EXISTS webhook_events (
    id              SERIAL PRIMARY KEY,
    webhook_id      VARCHAR(255) UNIQUE NOT NULL,  -- ID unique côté provider
    provider        VARCHAR(20) NOT NULL,           -- korapay | campay
    event_type      VARCHAR(100) NOT NULL,          -- ex: charge.completed
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending | processed | failed | skipped (déjà traité)
    raw_payload     JSONB NOT NULL,                -- Payload brut reçu (pour debug/replay)
    attempts        INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TIMESTAMP,
    processed_at    TIMESTAMP,
    error_detail    TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_webhook_events_provider_status ON webhook_events(provider, status);
CREATE INDEX IF NOT EXISTS idx_webhook_events_webhook_id ON webhook_events(webhook_id);

-- ─── TRIGGER updated_at AUTO ─────────────────────────────────────────────────
-- Réutilise ou crée la fonction générique de mise à jour

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS trg_payment_links_updated_at ON payment_links;
CREATE TRIGGER trg_payment_links_updated_at
    BEFORE UPDATE ON payment_links
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_payment_events_updated_at ON payment_events;
CREATE TRIGGER trg_payment_events_updated_at
    BEFORE UPDATE ON payment_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_webhook_events_updated_at ON webhook_events;
CREATE TRIGGER trg_webhook_events_updated_at
    BEFORE UPDATE ON webhook_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
