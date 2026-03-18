-- Migration : ajout response_delay/typing_indicator sur agent_templates
--             + création table outbound_tracking
-- Exécuter avec : psql -U neobot -d neobot_db -f add_outbound_tracking_and_agent_delay.sql

BEGIN;

-- 1. Colonnes response_delay et typing_indicator sur agent_templates
ALTER TABLE agent_templates
    ADD COLUMN IF NOT EXISTS response_delay VARCHAR(20) NOT NULL DEFAULT 'natural',
    ADD COLUMN IF NOT EXISTS typing_indicator BOOLEAN NOT NULL DEFAULT TRUE;

-- 2. Table outbound_tracking (enforcement max 2 messages sortants/contact)
CREATE TABLE IF NOT EXISTS outbound_tracking (
    id                          SERIAL PRIMARY KEY,
    tenant_id                   VARCHAR(50) NOT NULL,
    phone_number                VARCHAR(20) NOT NULL,

    -- Compteurs par type de trigger
    rdv_outbound_count          INTEGER NOT NULL DEFAULT 0,
    order_outbound_count        INTEGER NOT NULL DEFAULT 0,
    subscription_outbound_count INTEGER NOT NULL DEFAULT 0,
    promo_outbound_count        INTEGER NOT NULL DEFAULT 0,
    total_outbound_count        INTEGER NOT NULL DEFAULT 0,

    -- Dernier envoi
    last_outbound_at            TIMESTAMP WITH TIME ZONE,
    last_trigger_type           VARCHAR(50),

    -- Opt-out (réponse STOP)
    opted_out                   BOOLEAN NOT NULL DEFAULT FALSE,
    opted_out_at                TIMESTAMP WITH TIME ZONE,

    -- Fenêtre 24h pour calcul de fenêtre glissante (optionnel)
    window_start                TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Contrainte d'unicité : un seul enregistrement par (tenant, numéro)
    CONSTRAINT uq_outbound_tenant_phone UNIQUE (tenant_id, phone_number)
);

-- Index pour les requêtes de vérification fréquentes
CREATE INDEX IF NOT EXISTS idx_outbound_tracking_tenant_phone
    ON outbound_tracking (tenant_id, phone_number);

CREATE INDEX IF NOT EXISTS idx_outbound_tracking_opted_out
    ON outbound_tracking (tenant_id, opted_out);

-- Trigger pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_outbound_tracking_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_outbound_tracking_updated_at ON outbound_tracking;
CREATE TRIGGER trg_outbound_tracking_updated_at
    BEFORE UPDATE ON outbound_tracking
    FOR EACH ROW EXECUTE FUNCTION update_outbound_tracking_updated_at();

COMMIT;
