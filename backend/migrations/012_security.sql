-- ============================================================
-- Migration 012 — Sécurité production NeoBot
-- login_attempts, refresh_tokens, revoked_tokens, indexes
-- ============================================================

-- ── 1. Tracking des tentatives de connexion (anti-brute-force) ──────────────
CREATE TABLE IF NOT EXISTS login_attempts (
    id          SERIAL PRIMARY KEY,
    ip_address  VARCHAR(45)  NOT NULL,           -- IPv4 ou IPv6
    email       VARCHAR(255) NULL,               -- Email tenté (peut être NULL)
    success     BOOLEAN      NOT NULL DEFAULT FALSE,
    attempted_at TIMESTAMP   NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_login_attempts_ip_attempted_at
    ON login_attempts (ip_address, attempted_at);
CREATE INDEX IF NOT EXISTS ix_login_attempts_attempted_at
    ON login_attempts (attempted_at);

-- ── 2. Refresh tokens (rotation sécurisée, expiration 30j) ──────────────────
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(64)  NOT NULL UNIQUE,    -- SHA-256 du token
    revoked     BOOLEAN      NOT NULL DEFAULT FALSE,
    revoked_at  TIMESTAMP    NULL,
    expires_at  TIMESTAMP    NOT NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token_hash   ON refresh_tokens (token_hash);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id      ON refresh_tokens (user_id);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_expires_at   ON refresh_tokens (expires_at);

-- ── 3. Tokens JWT révoqués (logout avant expiration) ────────────────────────
-- On stocke le JTI + expiration pour purge automatique
CREATE TABLE IF NOT EXISTS revoked_tokens (
    id          SERIAL PRIMARY KEY,
    jti         VARCHAR(64)  NOT NULL UNIQUE,    -- Identifiant unique du JWT (champ "jti")
    user_id     INTEGER      NOT NULL,
    expires_at  TIMESTAMP    NOT NULL,           -- Copie de l'expiration du JWT
    revoked_at  TIMESTAMP    NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_revoked_tokens_jti        ON revoked_tokens (jti);
CREATE INDEX IF NOT EXISTS ix_revoked_tokens_expires_at ON revoked_tokens (expires_at);

-- ── 4. Index manquants sur les tables existantes ─────────────────────────────
-- conversations.tenant_id (requêtes fréquentes)
CREATE INDEX IF NOT EXISTS ix_conversations_tenant_id
    ON conversations (tenant_id);

-- subscriptions.tenant_id (middleware subscription vérifie par tenant_id)
-- (déjà unique=True donc index implicite, mais on s'assure)
CREATE INDEX IF NOT EXISTS ix_subscriptions_tenant_id
    ON subscriptions (tenant_id);

-- payment_events.transaction_id (lookups rapide lors des webhooks Korapay)
CREATE INDEX IF NOT EXISTS ix_payment_events_transaction_id
    ON payment_events (transaction_id);

-- messages.conversation_id (jointures fréquentes)
CREATE INDEX IF NOT EXISTS ix_messages_conversation_id
    ON messages (conversation_id);

-- messages.created_at (tri chronologique)
CREATE INDEX IF NOT EXISTS ix_messages_created_at
    ON messages (created_at);

-- users.tenant_id (lookup fréquent)
CREATE INDEX IF NOT EXISTS ix_users_tenant_id
    ON users (tenant_id);

-- ── 5. Purge auto des tentatives > 24h (appelée par cron) ───────────────────
-- Pas de cron ici — la purge est faite dans auth.py après chaque login
-- La requête de comptage est déjà filtrée sur attempted_at >= now() - interval '5 min'
-- L'index ix_login_attempts_attempted_at la rend O(log n) au lieu de O(n)
