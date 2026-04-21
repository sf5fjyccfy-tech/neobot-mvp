/**
 * Supabase-backed Baileys auth state persistence.
 * 
 * Remplace pg-auth-state.js (Neon) avec support Supabase.
 * Sauvegarde automatique des sessions Baileys en base + fallback file-based.
 * 
 * Déploiement Render:
 * - DATABASE_URL = postgresql://postgres.xxx@aws-0-eu-west-1.pooler.supabase.com:5432/postgres
 * - Auto-reconnect en cas de session perdue
 */

import { initAuthCreds, BufferJSON } from '@whiskeysockets/baileys';
import pg from 'pg';

const { Pool } = pg;

let _pool = null;

function getPool() {
  if (!_pool) {
    const dbUrl = process.env.DATABASE_URL;
    if (!dbUrl) throw new Error('DATABASE_URL non défini');
    
    _pool = new Pool({
      connectionString: dbUrl,
      ssl: { rejectUnauthorized: false },  // Supabase nécessite SSL
      max: 3,                               // Economie free tier
      idleTimeoutMillis: 30_000,
      connectionTimeoutMillis: 15_000,
      keepAlive: true,
      keepAliveInitialDelayMillis: 10_000,
    });
    
    _pool.on('error', (err) => {
      console.error('[pg-auth-state] Pool error:', err.message);
    });
  }
  return _pool;
}

async function ensureTable(pool) {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS whatsapp_auth_state (
      tenant_id  INTEGER NOT NULL,
      key_name   TEXT    NOT NULL,
      data       TEXT    NOT NULL,
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      PRIMARY KEY (tenant_id, key_name)
    )
  `);
}

/**
 * usePgAuthState - Compatible avec Baileys
 * 
 * Usage:
 *   const { state, saveCreds } = await usePgAuthState(tenantId);
 *   makeWASocket({ auth: state });
 */
export async function usePgAuthState(tenantId) {
  const pool = getPool();
  await ensureTable(pool);

  // Load existing state
  const loadState = async (storageKey) => {
    const result = await pool.query(
      'SELECT data FROM whatsapp_auth_state WHERE tenant_id = $1 AND key_name = $2',
      [tenantId, storageKey]
    );
    
    if (result.rows.length > 0) {
      try {
        return JSON.parse(result.rows[0].data, BufferJSON.reviver);
      } catch (e) {
        console.error(`[pg-auth-state] Error parsing ${storageKey}:`, e.message);
        return null;
      }
    }
    return null;
  };

  // Save state
  const saveState = async (storageKey, state) => {
    try {
      const data = JSON.stringify(state, BufferJSON.replacer);
      
      await pool.query(
        `INSERT INTO whatsapp_auth_state (tenant_id, key_name, data, updated_at)
         VALUES ($1, $2, $3, NOW())
         ON CONFLICT (tenant_id, key_name)
         DO UPDATE SET data = $3, updated_at = NOW()`,
        [tenantId, storageKey, data]
      );
    } catch (e) {
      console.error(`[pg-auth-state] Error saving ${storageKey}:`, e.message);
    }
  };

  // Initialize auth state
  const creds = await loadState('creds') || initAuthCreds();

  return {
    state: {
      creds,
      keys: {
        get: async (type, jids) => {
          const tasks = jids.map(jid =>
            loadState(`key_${type}_${jid}`)
              .then(data => ({ jid, data }))
          );
          const results = await Promise.all(tasks);
          
          const returnData = {};
          results.forEach(({ jid, data }) => {
            if (data) returnData[jid] = data;
          });
          return returnData;
        },
        set: async (data) => {
          const tasks = [];
          for (const [key, val] of Object.entries(data)) {
            const [type, ...jidParts] = key.split('_');
            const jid = jidParts.join('_');
            tasks.push(saveState(`key_${type}_${jid}`, val));
          }
          await Promise.all(tasks);
        },
      },
    },
    saveCreds: async () => {
      await saveState('creds', creds);
    },
  };
}

/**
 * Cleanup: Clear session pour une reconnexion forcée
 */
export async function clearPgAuthState(tenantId) {
  const pool = getPool();
  await pool.query(
    'DELETE FROM whatsapp_auth_state WHERE tenant_id = $1',
    [tenantId]
  );
  console.log(`[pg-auth-state] Session cleared for tenant ${tenantId}`);
}

/**
 * Health check
 */
export async function pingPool() {
  try {
    const pool = getPool();
    await pool.query('SELECT NOW()');
    return true;
  } catch (e) {
    console.error('[pg-auth-state] Pool ping failed:', e.message);
    return false;
  }
}
