-- Migration 009: ajouter le tracking des outcomes (résultats) aux conversations
-- outcome_type : null (pas encore détecté), 'rdv_pris', 'vente', 'lead_qualifié',
--               'support_résolu', 'désintérêt'

ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS outcome_type VARCHAR(50) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS outcome_detected_at TIMESTAMP DEFAULT NULL;

-- Index pour les requêtes de stats par tenant + outcome
CREATE INDEX IF NOT EXISTS idx_conversations_tenant_outcome
    ON conversations(tenant_id, outcome_type);
