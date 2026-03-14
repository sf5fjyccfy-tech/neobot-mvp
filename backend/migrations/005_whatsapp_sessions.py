"""
WhatsApp Sessions Table Migration
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

# Pour exécuter cette migration:
# psql neobot_db -c """
# CREATE TABLE IF NOT EXISTS whatsapp_sessions (
#     id SERIAL PRIMARY KEY,
#     tenant_id INTEGER NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
#     whatsapp_phone VARCHAR(50) NOT NULL UNIQUE,
#     baileys_session_file TEXT,
#     is_connected BOOLEAN DEFAULT false,
#     last_connected_at TIMESTAMP,
#     failed_attempts INTEGER DEFAULT 0,
#     created_at TIMESTAMP DEFAULT NOW(),
#     updated_at TIMESTAMP DEFAULT NOW()
# );
# """

SQL_MIGRATION = """
-- Create WhatsApp Sessions table
-- Maps phone numbers to tenants for Baileys multi-device integration

CREATE TABLE IF NOT EXISTS whatsapp_sessions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
    whatsapp_phone VARCHAR(50) NOT NULL UNIQUE,
    baileys_session_file TEXT,
    is_connected BOOLEAN DEFAULT false,
    last_connected_at TIMESTAMP,
    failed_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_whatsapp_sessions_phone ON whatsapp_sessions(whatsapp_phone);
CREATE INDEX IF NOT EXISTS idx_whatsapp_sessions_tenant_id ON whatsapp_sessions(tenant_id);
"""

print("Migration SQL ready. Run with:")
print("psql neobot_db < migration.sql")
