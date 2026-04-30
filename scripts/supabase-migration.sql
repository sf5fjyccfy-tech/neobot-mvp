-- NeoBot — Schema complet Supabase
-- Exécute dans Supabase SQL Editor (idempotent — peut être relancé sans danger)

-- 0. Types Enum PostgreSQL (requis avant les tables qui les utilisent)
DO $$ BEGIN CREATE TYPE plantype AS ENUM ('NEOBOT','BASIC','STANDARD','PRO'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE agenttype AS ENUM ('libre','rdv','support','faq','vente','qualification'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE knowledgesourcetype AS ENUM ('url','pdf','youtube','faq','text'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE conversationstatus AS ENUM ('active','pending','closed','archived'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE businesstype AS ENUM ('neobot','restaurant','ecommerce','travel','salon','fitness','consulting','custom'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- 1. TENANTS
CREATE TABLE IF NOT EXISTS tenants (
    id                     SERIAL PRIMARY KEY,
    name                   VARCHAR(255) NOT NULL,
    email                  VARCHAR(255) UNIQUE NOT NULL,
    phone                  VARCHAR(50) NOT NULL,
    business_type          VARCHAR(100) DEFAULT 'autre',
    plan                   VARCHAR(50) DEFAULT 'BASIC',
    whatsapp_provider      VARCHAR(50) DEFAULT 'WASENDER_API',
    whatsapp_connected     BOOLEAN DEFAULT false,
    messages_used          INTEGER DEFAULT 0,
    messages_limit         INTEGER DEFAULT 2500,
    is_trial               BOOLEAN DEFAULT true,
    trial_ends_at          TIMESTAMP WITH TIME ZONE,
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    is_suspended           BOOLEAN DEFAULT false,
    suspension_reason      TEXT,
    suspended_at           TIMESTAMP WITH TIME ZONE,
    is_deleted             BOOLEAN DEFAULT false,
    deleted_at             TIMESTAMP WITH TIME ZONE,
    messages_period_start  TIMESTAMP WITH TIME ZONE,
    created_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. USERS
CREATE TABLE IF NOT EXISTS users (
    id                       SERIAL PRIMARY KEY,
    tenant_id                INTEGER NOT NULL REFERENCES tenants(id),
    email                    VARCHAR(255) UNIQUE NOT NULL,
    hashed_password          VARCHAR(255) NOT NULL,
    full_name                VARCHAR(255),
    role                     VARCHAR(50) DEFAULT 'user',
    is_superadmin            BOOLEAN DEFAULT false,
    is_active                BOOLEAN DEFAULT true,
    created_at               TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login               TIMESTAMP WITH TIME ZONE,
    totp_secret              VARCHAR(64),
    totp_enabled             BOOLEAN DEFAULT false,
    email_verified           BOOLEAN DEFAULT false,
    email_verification_token VARCHAR(255) UNIQUE,
    reset_token              VARCHAR(255) UNIQUE,
    reset_token_expires_at   TIMESTAMP WITH TIME ZONE
);

-- 3. CONTACTS
CREATE TABLE IF NOT EXISTS contacts (
    id                SERIAL PRIMARY KEY,
    tenant_id         INTEGER NOT NULL REFERENCES tenants(id),
    phone             VARCHAR(50) NOT NULL,
    name              VARCHAR(255),
    is_whitelisted    BOOLEAN DEFAULT false,
    is_blacklisted    BOOLEAN DEFAULT false,
    is_active         BOOLEAN DEFAULT true,
    first_contact_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_contact_date  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    message_count     INTEGER DEFAULT 0,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. CONVERSATIONS & MESSAGES
CREATE TABLE IF NOT EXISTS conversations (
    id                  SERIAL PRIMARY KEY,
    tenant_id           INTEGER NOT NULL REFERENCES tenants(id),
    customer_phone      VARCHAR(50) NOT NULL,
    customer_name       VARCHAR(255),
    channel             VARCHAR(50) DEFAULT 'whatsapp',
    status              VARCHAR(50) DEFAULT 'active',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    outcome_type        VARCHAR(50),
    outcome_detected_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS messages (
    id              SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id),
    content         TEXT NOT NULL,
    direction       VARCHAR(20) NOT NULL,
    is_ai           BOOLEAN DEFAULT false,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. WHATSAPP
CREATE TABLE IF NOT EXISTS whatsapp_auth_state (
    tenant_id  INTEGER NOT NULL,
    key_name   TEXT NOT NULL,
    data       TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (tenant_id, key_name)
);

CREATE TABLE IF NOT EXISTS whatsapp_sessions (
    id               SERIAL PRIMARY KEY,
    tenant_id        INTEGER NOT NULL,
    whatsapp_phone   VARCHAR(50),
    connection_status VARCHAR(50) DEFAULT 'idle',
    connected_at     TIMESTAMP WITH TIME ZONE,
    disconnected_at  TIMESTAMP WITH TIME ZONE,
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS whatsapp_session_qrs (
    id         SERIAL PRIMARY KEY,
    tenant_id  INTEGER NOT NULL,
    qr_data    TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. SUBSCRIPTIONS (schéma complet — conforme au modèle SQLAlchemy)
CREATE TABLE IF NOT EXISTS subscriptions (
    id                     SERIAL PRIMARY KEY,
    tenant_id              INTEGER NOT NULL UNIQUE REFERENCES tenants(id),
    plan                   VARCHAR(50) NOT NULL,
    status                 VARCHAR(50) DEFAULT 'active',
    is_trial               BOOLEAN DEFAULT true,
    trial_start_date       TIMESTAMP WITH TIME ZONE,
    trial_end_date         TIMESTAMP WITH TIME ZONE NOT NULL,
    subscription_start_date TIMESTAMP WITH TIME ZONE,
    subscription_end_date  TIMESTAMP WITH TIME ZONE,
    cancelled_at           TIMESTAMP WITH TIME ZONE,
    next_billing_date      TIMESTAMP WITH TIME ZONE,
    last_billing_date      TIMESTAMP WITH TIME ZONE,
    auto_renew             BOOLEAN DEFAULT true,
    created_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. AGENTS & KNOWLEDGE
CREATE TABLE IF NOT EXISTS agent_templates (
    id              SERIAL PRIMARY KEY,
    tenant_id       INTEGER REFERENCES tenants(id),
    name            VARCHAR(255) NOT NULL,
    agent_type      VARCHAR(50),
    system_prompt   TEXT,
    is_active       BOOLEAN DEFAULT true,
    response_delay_seconds INTEGER DEFAULT 0,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_sources (
    id          SERIAL PRIMARY KEY,
    tenant_id   INTEGER NOT NULL REFERENCES tenants(id),
    agent_id    INTEGER REFERENCES agent_templates(id),
    source_type VARCHAR(50) NOT NULL,
    title       VARCHAR(255),
    content     TEXT,
    url         VARCHAR(2048),
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. PAYMENTS
CREATE TABLE IF NOT EXISTS payment_events (
    id          SERIAL PRIMARY KEY,
    tenant_id   INTEGER NOT NULL REFERENCES tenants(id),
    event_type  VARCHAR(50),
    amount      DECIMAL(10,2),
    currency    VARCHAR(3),
    reference   VARCHAR(255),
    status      VARCHAR(50),
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. SECURITY & AUTH
CREATE TABLE IF NOT EXISTS login_attempts (
    id           SERIAL PRIMARY KEY,
    ip_address   VARCHAR(45) NOT NULL,
    email        VARCHAR(255),
    success      BOOLEAN NOT NULL DEFAULT false,
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    token_hash VARCHAR(64) UNIQUE NOT NULL,
    revoked    BOOLEAN NOT NULL DEFAULT false,
    revoked_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS revoked_tokens (
    id         SERIAL PRIMARY KEY,
    jti        VARCHAR(64) UNIQUE NOT NULL,
    user_id    INTEGER NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. INDEXES (performance)
CREATE INDEX IF NOT EXISTS idx_tenants_email ON tenants(email);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_conversations_tenant ON conversations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_conversations_phone ON conversations(customer_phone);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX IF NOT EXISTS idx_login_attempts_at ON login_attempts(attempted_at);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_revoked_tokens_jti ON revoked_tokens(jti);

-- 11. AUTO-CORRECTIONS pour bases existantes avec schéma partiel
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(64);
ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superadmin BOOLEAN DEFAULT false;

ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS plan VARCHAR(50);
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS is_trial BOOLEAN DEFAULT true;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS trial_start_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS trial_end_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS subscription_start_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS next_billing_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS auto_renew BOOLEAN DEFAULT true;

ALTER TABLE login_attempts ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE login_attempts ADD COLUMN IF NOT EXISTS attempted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

SELECT 'Schema NeoBot OK' AS status;
