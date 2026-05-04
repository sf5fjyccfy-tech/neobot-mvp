-- Migration 014: Références NEO + tokens de confirmation sur payment_events
-- Date: 2026-05-03
-- Purpose: Ajouter neo_ref (NEO-YYYY-NNNN), confirm_token (lien email 1-clic),
--          confirm_token_expires_at et confirmed_at sur la table payment_events.

ALTER TABLE payment_events
    ADD COLUMN IF NOT EXISTS neo_ref                  VARCHAR(20)  UNIQUE,
    ADD COLUMN IF NOT EXISTS confirm_token            VARCHAR(64)  UNIQUE,
    ADD COLUMN IF NOT EXISTS confirm_token_expires_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS confirmed_at             TIMESTAMP;

-- Index pour les lookups par token (endpoint confirm-payment)
CREATE UNIQUE INDEX IF NOT EXISTS idx_payment_events_confirm_token
    ON payment_events (confirm_token)
    WHERE confirm_token IS NOT NULL;

-- Index pour les lookups par ref
CREATE UNIQUE INDEX IF NOT EXISTS idx_payment_events_neo_ref
    ON payment_events (neo_ref)
    WHERE neo_ref IS NOT NULL;
