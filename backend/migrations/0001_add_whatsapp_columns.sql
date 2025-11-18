ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS whatsapp_messages_used integer NOT NULL DEFAULT 0;
ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS other_messages_used integer NOT NULL DEFAULT 0;
ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS whatsapp_provider text;
ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS whatsapp_connected boolean NOT NULL DEFAULT false;
ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS whatsapp_config jsonb DEFAULT '{}'::jsonb;