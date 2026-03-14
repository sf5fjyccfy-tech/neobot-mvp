-- Overages Table Migration
-- Tracks billing overages when usage exceeds plan limits

CREATE TABLE IF NOT EXISTS overages (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    month_year VARCHAR(7) NOT NULL,  -- "2026-02"
    messages_over INTEGER DEFAULT 0,
    cost_fcfa INTEGER DEFAULT 0,
    is_billed BOOLEAN DEFAULT false,
    billed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, month_year)
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_overages_tenant_id ON overages(tenant_id);
CREATE INDEX IF NOT EXISTS idx_overages_month_year ON overages(month_year);
CREATE INDEX IF NOT EXISTS idx_overages_is_billed ON overages(is_billed);

-- This migration enables:
-- 1. Overage pricing tracking (1000 messages = 7000 FCFA)
-- 2. Billing management
-- 3. Customer invoicing
-- 4. Financial reporting
