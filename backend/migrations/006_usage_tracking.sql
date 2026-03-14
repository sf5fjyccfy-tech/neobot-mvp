-- Usage Tracking Table Migration
-- Tracks daily and monthly message usage per tenant

CREATE TABLE IF NOT EXISTS usage_tracking (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    month_year VARCHAR(7) NOT NULL,  -- "2026-02"
    whatsapp_messages_used INTEGER DEFAULT 0,
    other_platform_messages_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, month_year)
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_usage_tracking_tenant_id ON usage_tracking(tenant_id);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_month_year ON usage_tracking(month_year);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_tenant_month ON usage_tracking(tenant_id, month_year);

-- This migration enables:
-- 1. Monthly message usage tracking per tenant
-- 2. Multi-platform support (WhatsApp + others)
-- 3. Usage reset at month boundaries
-- 4. Quota checking for overage pricing
