-- Migration 008: agrandir les colonnes trop courtes dans tenant_business_config
-- selling_focus était VARCHAR(255) → TEXT (peut contenir des fiches produit longues)

ALTER TABLE tenant_business_config
    ALTER COLUMN selling_focus TYPE TEXT;

-- Aussi nettoyer les éventuels products_services double-encodés (string JSON dans JSONB)
-- Si la valeur stockée est un string et non un objet JSON, on le redécode
UPDATE tenant_business_config
SET products_services = (products_services #>> '{}')::jsonb
WHERE jsonb_typeof(products_services) = 'string';
