-- Migration: Add Business Intelligence System
-- Date: 2026-02-11
-- Description: Create tables for multi-business support and intelligent context

-- =========================================================
-- 1. CREATE TABLE: business_types
-- =========================================================
-- Types de business (Restaurant, E-commerce, Travel, etc)

CREATE TABLE IF NOT EXISTS business_types (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(slug)
);

-- Index pour les recherches rapides
CREATE INDEX IF NOT EXISTS idx_business_types_slug ON business_types(slug);

-- =========================================================
-- 2. CREATE TABLE: tenant_business_config
-- =========================================================
-- Configuration personnalisée par tenant

CREATE TABLE IF NOT EXISTS tenant_business_config (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    business_type_id INTEGER NOT NULL,
    company_name VARCHAR(255),
    company_description TEXT,
    products_services JSONB,
    tone VARCHAR(50),
    selling_focus VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (business_type_id) REFERENCES business_types(id) ON DELETE CASCADE,
    UNIQUE(tenant_id)
);

-- Index pour recherches rapides
CREATE INDEX IF NOT EXISTS idx_tenant_business_config_tenant_id ON tenant_business_config(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_business_config_business_type_id ON tenant_business_config(business_type_id);

-- =========================================================
-- 3. CREATE TABLE: conversation_context
-- =========================================================
-- Contexte amélioré pour chaque conversation

CREATE TABLE IF NOT EXISTS conversation_context (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    config_id INTEGER,
    client_name VARCHAR(255),
    client_previous_interest JSONB,
    conversation_stage VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (config_id) REFERENCES tenant_business_config(id) ON DELETE SET NULL,
    UNIQUE(conversation_id)
);

-- Index pour recherches rapides
CREATE INDEX IF NOT EXISTS idx_conversation_context_conversation_id ON conversation_context(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversation_context_config_id ON conversation_context(config_id);

-- =========================================================
-- 4. INSERT DEFAULT BUSINESS TYPES
-- =========================================================

INSERT INTO business_types (slug, name, description, icon) VALUES
    ('neobot', 'NéoBot Service', 'Vendre NéoBot lui-même', '🤖'),
    ('restaurant', 'Restaurant', 'Café, restaurant, fast-food', '🍽️'),
    ('ecommerce', 'E-commerce', 'Boutique en ligne, vente produits', '🛍️'),
    ('travel', 'Agence de Voyage', 'Tours, hôtels, packages vacances', '✈️'),
    ('salon', 'Salon de Beauté', 'Coiffure, massage, esthétique', '💇'),
    ('fitness', 'Fitness', 'Gym, yoga, entraînement', '💪'),
    ('consulting', 'Consulting', 'Services de consultation professionnels', '📊'),
    ('custom', 'Custom', 'Configuration personnalisée', '⚙️')
ON CONFLICT (slug) DO NOTHING;

-- =========================================================
-- VERIFICATION
-- =========================================================
-- Vérifier que les tables ont été créées

SELECT 'Migration completed successfully!' as status,
       (SELECT COUNT(*) FROM business_types) as business_types_count,
       (SELECT COUNT(*) FROM tenant_business_config) as config_count,
       (SELECT COUNT(*) FROM conversation_context) as context_count;
