/**
 * PostgreSQL-backed Baileys auth state.
 *
 * Remplace useMultiFileAuthState (filesystem) par une persistance en base de
 * données PostgreSQL (Neon). Chaque credential ou clé Signal est stocké comme
 * une ligne (tenant_id, key_name, data JSONB).
 *
 * Table auto-créée au premier appel — pas de migration nécessaire.
 */

import { initAuthCreds, BufferJSON } from '@whiskeysockets/baileys';
import pg from 'pg';

const { Pool } = pg;

// Pool partagé entre tous les tenants (singleton)
let _pool = null;

function getPool() {
  if (!_pool) {
    const dbUrl = process.env.DATABASE_URL;
    if (!dbUrl) throw new Error('DATABASE_URL non défini — impossible d\'utiliser pg-auth-state');
    _pool = new Pool({
      connectionString: dbUrl,
      ssl: { rejectUnauthorized: false }, // requis pour Neon
      max: 3,                             // 5→3 : économise ~30MB sur free tier 512MB
      idleTimeoutMillis: 30_000,
      connectionTimeoutMillis: 15_000,    // 5→15s : Neon cold start peut prendre jusqu'à 10s
      keepAlive: true,                    // évite les connexions stagnantes coupées par Neon
      keepAliveInitialDelayMillis: 10_000,
    });
    _pool.on('error', (err) => {
      console.error('[pg-auth-state] pool error:', err.message);
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
      updated_at TIMESTAMPTZ DEFAULT NOW(),
      PRIMARY KEY (tenant_id, key_name)
    )
  `);
}

async function readData(pool, tenantId, keyName) {
  const res = await pool.query(
    'SELECT data FROM whatsapp_auth_state WHERE tenant_id=$1 AND key_name=$2',
    [tenantId, keyName]
  );
  if (!res.rows[0]) return null;
  try {
    return JSON.parse(res.rows[0].data, BufferJSON.reviver);
  } catch {
    return null;
  }
}

async function writeData(pool, tenantId, keyName, data) {
  if (data === null || data === undefined) {
    await pool.query(
      'DELETE FROM whatsapp_auth_state WHERE tenant_id=$1 AND key_name=$2',
      [tenantId, keyName]
    );
  } else {
    const serialized = JSON.stringify(data, BufferJSON.replacer);
    await pool.query(
      `INSERT INTO whatsapp_auth_state (tenant_id, key_name, data, updated_at)
       VALUES ($1, $2, $3, NOW())
       ON CONFLICT (tenant_id, key_name)
       DO UPDATE SET data=$3, updated_at=NOW()`,
      [tenantId, keyName, serialized]
    );
  }
}

/**
 * Équivalent de useMultiFileAuthState mais en PostgreSQL.
 *
 * @param {number} tenantId
 * @returns {{ state: { creds, keys }, saveCreds }}
 */
export async function usePgAuthState(tenantId) {
  const pool = getPool();
  await ensureTable(pool);

  // Charger les creds existants ou initialiser de nouveaux
  const storedCreds = await readData(pool, tenantId, 'creds');
  const creds = storedCreds ?? initAuthCreds();

  const state = {
    creds,
    keys: {
      async get(type, ids) {
        const data = {};
        for (const id of ids) {
          const value = await readData(pool, tenantId, `${type}-${id}`);
          if (value !== null) {
            data[id] = value;
          }
        }
        return data;
      },

      async set(data) {
        const writes = [];
        for (const [type, entries] of Object.entries(data)) {
          for (const [id, value] of Object.entries(entries)) {
            writes.push(writeData(pool, tenantId, `${type}-${id}`, value));
          }
        }
        await Promise.all(writes);
      },
    },
  };

  // saveCreds lit state.creds qui est muté in-place par Baileys
  const saveCreds = () => writeData(pool, tenantId, 'creds', state.creds);

  return { state, saveCreds };
}

/**
 * Supprimer tous les credentials d'un tenant (équivalent de rm -rf auth_info_baileys/tenant_X)
 *
 * @param {number} tenantId
 */
export async function clearPgAuthState(tenantId) {
  const pool = getPool();
  await pool.query(
    'DELETE FROM whatsapp_auth_state WHERE tenant_id=$1',
    [tenantId]
  );
}

/**
 * Keep-alive : évite que Neon suspende la connexion pendant les périodes d'inactivité WA.
 * À appeler toutes les 4 minutes via setInterval dans le service.
 */
export async function pingPool() {
  if (!_pool) return; // pool non encore créé, pas la peine de ping
  try {
    await _pool.query('SELECT 1');
  } catch (err) {
    console.warn('[pg-auth-state] keep-alive ping failed:', err.message);
  }
}
