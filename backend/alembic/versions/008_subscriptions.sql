-- Migration 008: Subscriptions & Trial Management
-- Date: 2026-01-01
-- Purpose: Track tenant subscription plans, trial periods, and upgrade status

CREATE TABLE subscriptions (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
  
  -- Plan information
  plan VARCHAR(50) NOT NULL CHECK (plan IN ('basique', 'standard', 'pro')),
  status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'cancelled')),
  
  -- Trial information
  is_trial BOOLEAN NOT NULL DEFAULT TRUE,
  trial_start_date DATE NOT NULL,
  trial_end_date DATE NOT NULL,
  
  -- Subscription dates
  subscription_start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  subscription_end_date TIMESTAMP,
  cancelled_at TIMESTAMP,
  
  -- Billing information
  next_billing_date DATE,
  last_billing_date DATE,
  auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
  
  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  -- Constraints
  CONSTRAINT valid_trial_dates CHECK (trial_end_date >= trial_start_date),
  CONSTRAINT plan_required CHECK (plan IS NOT NULL)
);

-- Create index on tenant_id for fast lookups
CREATE INDEX idx_subscriptions_tenant_id ON subscriptions(tenant_id);
CREATE INDEX idx_subscriptions_plan ON subscriptions(plan);
CREATE INDEX idx_subscriptions_is_trial ON subscriptions(is_trial);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_subscriptions_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_subscriptions_timestamp
BEFORE UPDATE ON subscriptions
FOR EACH ROW
EXECUTE FUNCTION update_subscriptions_timestamp();

-- Add comment
COMMENT ON TABLE subscriptions IS 'Tracks subscription plans, trial periods, and billing information for each tenant';
COMMENT ON COLUMN subscriptions.is_trial IS 'TRUE if tenant is still in trial period, FALSE if they have paid subscription';
COMMENT ON COLUMN subscriptions.plan IS 'Active plan: basique (2K msgs), standard (2.5K msgs), pro (40K msgs)';
