-- NeoBot Migration Script: Neon → Supabase
-- Exécute ceci dans Supabase SQL Editor (tout en une fois)
-- Crée les tables et les structures nécessaires

-- 1. TABLES CORE
CREATE TABLE IF NOT EXISTS tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50) NOT NULL,
    business_type VARCHAR(100) DEFAULT 'autre',
    plan VARCHAR(50) DEFAULT 'BASIC',
    whatsapp_provider VARCHAR(50) DEFAULT 'WASENDER_API',
    whatsapp_connected BOOLEAN DEFAULT false,
    messages_used INTEGER DEFAULT 0,
    messages_limit INTEGER DEFAULT 2500,
    is_trial BOOLEAN DEFAULT true,
    trial_ends_at TIMESTAMP WITH TIME ZONE,
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    is_suspended BOOLEAN DEFAULT false,
    suspension_reason TEXT,
    suspended_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    messages_period_start TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_superadmin BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    totp_secret VARCHAR(64),
    totp_enabled BOOLEAN DEFAULT false,
    email_verified BOOLEAN DEFAULT false,
    email_verification_token VARCHAR(255) UNIQUE,
    reset_token VARCHAR(255) UNIQUE,
    reset_token_expires_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    customer_phone VARCHAR(50) NOT NULL,
    customer_name VARCHAR(255),
    channel VARCHAR(50) DEFAULT 'whatsapp',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    outcome_type VARCHAR(50),
    outcome_detected_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id),
    content TEXT NOT NULL,
    direction VARCHAR(20) NOT NULL,
    is_ai BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. WHATSAPP AUTH PERSISTENCE (BAILEYS)
CREATE TABLE IF NOT EXISTS whatsapp_auth_state (
    tenant_id INTEGER NOT NULL,
    key_name TEXT NOT NULL,
    data TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (tenant_id, key_name)
);

CREATE TABLE IF NOT EXISTS whatsapp_sessions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    whatsapp_phone VARCHAR(50),
    connection_status VARCHAR(50) DEFAULT 'idle',
    connected_at TIMESTAMP WITH TIME ZONE,
    disconnected_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. CONFIG & SETTINGS
CREATE TABLE IF NOT EXISTS tenant_settings (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL UNIQUE REFERENCES tenants(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50),
    prompt_template TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. SUBSCRIPTIONS & PAYMENTS
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    plan_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payment_events (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    event_type VARCHAR(50),
    amount DECIMAL(10,2),
    currency VARCHAR(3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. MONITORING & TRACKING
CREATE TABLE IF NOT EXISTS usage_tracking (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    metric_name VARCHAR(100),
    metric_value INTEGER,
    tracked_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS login_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    ip_address VARCHAR(50),
    success BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. INDEXES (performance)
CREATE INDEX idx_tenants_email ON tenants(email);
CREATE INDEX idx_tenants_business_type ON tenants(business_type);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_conversations_tenant_id ON conversations(tenant_id);
CREATE INDEX idx_conversations_customer_phone ON conversations(customer_phone);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_whatsapp_sessions_tenant_id ON whatsapp_sessions(tenant_id);
CREATE INDEX idx_subscriptions_tenant_id ON subscriptions(tenant_id);
CREATE INDEX idx_payment_events_tenant_id ON payment_events(tenant_id);

-- 7. DONE
SELECT 'Schema NeoBot créé avec succès dans Supabase!' as status;
