// ╔════════════════════════════════════════════════════════════════════╗
// ║                                                                    ║
// ║      API de Gestion de Sessions WhatsApp pour NéoBot              ║
// ║                                                                    ║
// ║  Endpoints pour réinitialiser, supprimer et monitorer les         ║
// ║  sessions WhatsApp avec gestion d'erreurs automatique             ║
// ║                                                                    ║
// ╚════════════════════════════════════════════════════════════════════╝

import axios from 'axios';
import fs from 'fs';
import path from 'path';

// ========== CONFIGURATION ==========
const WHATSAPP_DIR = './auth_info_baileys';
const BACKUP_DIR = './.wwebjs_auth';
const SESSION_DIR = './session';
const API_TIMEOUT = 5000;

// ========== GESTION DES SESSIONS ==========

/**
 * Réinitialiser complètement une session
 * Supprime tous les fichiers et attends un nouveau QR code
 */
export async function resetSessionAPI(socketInstance, tenantId = 1) {
    console.log(`🔄 [API] Réinitialisation de la session tenant ${tenantId}`);
    
    try {
        // 1. Fermer la connexion
        await socketInstance.end();
        
        // 2. Supprimer les fichiers
        const dirsToClean = [WHATSAPP_DIR, BACKUP_DIR, SESSION_DIR];
        for (const dir of dirsToClean) {
            if (fs.existsSync(dir)) {
                fs.rmSync(dir, { recursive: true, force: true });
                console.log(`   ✅ Supprimé: ${dir}`);
            }
        }
        
        console.log(`✅ [API] Session réinitialisée - Nouveau QR en attente`);
        return {
            status: 'success',
            message: 'Session réinitialisée avec succès',
            nextAction: 'Veuillez attendre le nouveau QR code',
            tenantId
        };
    } catch (error) {
        console.error(`❌ [API] Erreur reset session:`, error.message);
        return {
            status: 'error',
            message: 'Erreur lors de la réinitialisation',
            error: error.message,
            tenantId
        };
    }
}

/**
 * Supprimer une session spécifique pour un tenant
 */
export async function deleteSessionForTenant(tenantId) {
    console.log(`🗑️  [API] Suppression de la session tenant ${tenantId}`);
    
    try {
        const sessionFile = path.join(WHATSAPP_DIR, `session_${tenantId}.json`);
        
        if (fs.existsSync(sessionFile)) {
            fs.unlinkSync(sessionFile);
            console.log(`   ✅ Fichier supprimé: ${sessionFile}`);
        }
        
        return {
            status: 'success',
            message: `Session supprimée pour tenant ${tenantId}`,
            tenantId
        };
    } catch (error) {
        console.error(`❌ [API] Erreur suppression session:`, error.message);
        return {
            status: 'error',
            message: 'Erreur lors de la suppression',
            error: error.message,
            tenantId
        };
    }
}

/**
 * Obtenir l'état de toutes les sessions
 */
export function getSessionsInfo() {
    console.log(`📊 [API] Lecture des informations de sessions`);
    
    const sessions = {};
    
    try {
        if (fs.existsSync(WHATSAPP_DIR)) {
            const files = fs.readdirSync(WHATSAPP_DIR);
            files.forEach(file => {
                const filePath = path.join(WHATSAPP_DIR, file);
                const stats = fs.statSync(filePath);
                sessions[file] = {
                    size: stats.size,
                    created: stats.birthtime,
                    modified: stats.mtime
                };
            });
        }
        
        return {
            status: 'success',
            sessions,
            count: Object.keys(sessions).length,
            timestamp: new Date().toISOString()
        };
    } catch (error) {
        console.error(`❌ [API] Erreur lecture sessions:`, error.message);
        return {
            status: 'error',
            message: 'Erreur lors de la lecture des sessions',
            error: error.message
        };
    }
}

/**
 * Vérifier si une session est expirée
 */
export function isSessionExpired(tenantId = 1) {
    console.log(`⏱️  [API] Vérification expiration session tenant ${tenantId}`);
    
    try {
        const authFile = path.join(WHATSAPP_DIR, 'creds.json');
        
        if (!fs.existsSync(authFile)) {
            return {
                status: 'expired',
                message: 'Pas de session active',
                tenantId,
                hasCredentials: false
            };
        }
        
        const stats = fs.statSync(authFile);
        const ageSeconds = (Date.now() - stats.mtimeMs) / 1000;
        const ageHours = ageSeconds / 3600;
        
        // Session expirée après 24 heures sans activité
        const isExpired = ageHours > 24;
        
        return {
            status: isExpired ? 'expired' : 'active',
            message: isExpired ? 'Session expirée' : 'Session active',
            tenantId,
            hasCredentials: true,
            ageHours: ageHours.toFixed(2),
            lastModified: stats.mtime.toISOString()
        };
    } catch (error) {
        console.error(`❌ [API] Erreur vérification:`, error.message);
        return {
            status: 'error',
            message: 'Erreur lors de la vérification',
            error: error.message,
            tenantId
        };
    }
}

/**
 * Nettoyer tous les fichiers temporaires
 */
export function cleanupTempFiles() {
    console.log(`🧹 [API] Nettoyage des fichiers temporaires`);
    
    try {
        const tempPatterns = [
            'session_history.log',
            'whatsapp.log',
            'error.log',
            '.DS_Store'
        ];
        
        let cleaned = 0;
        tempPatterns.forEach(pattern => {
            if (fs.existsSync(pattern)) {
                fs.unlinkSync(pattern);
                cleaned++;
                console.log(`   ✅ Supprimé: ${pattern}`);
            }
        });
        
        return {
            status: 'success',
            message: `${cleaned} fichiers temporaires supprimés`,
            filesRemoved: cleaned,
            timestamp: new Date().toISOString()
        };
    } catch (error) {
        console.error(`❌ [API] Erreur cleanup:`, error.message);
        return {
            status: 'error',
            message: 'Erreur lors du nettoyage',
            error: error.message
        };
    }
}

/**
 * Tracer les erreurs 405 et nettoyer automatiquement
 */
export async function handle405Error(socketInstance) {
    console.log(`🚨 [API] Erreur 405 détectée - Auto-cleanup en cours`);
    
    try {
        // 1. Fermer la connexion actuelle
        await socketInstance.end().catch(() => {});
        
        // 2. Nettoyer les fichiers temporaires
        cleanupTempFiles();
        
        // 3. Supprimer les sessions
        const dirsToClean = [WHATSAPP_DIR, BACKUP_DIR, SESSION_DIR];
        for (const dir of dirsToClean) {
            if (fs.existsSync(dir)) {
                fs.rmSync(dir, { recursive: true, force: true });
            }
        }
        
        console.log(`✅ [API] Auto-cleanup de l'erreur 405 terminé`);
        return {
            status: 'recovered',
            message: 'Auto-cleanup terminé - Redémarrage imminent',
            action: 'reconnect'
        };
    } catch (error) {
        console.error(`❌ [API] Erreur durante l'auto-cleanup:`, error.message);
        return {
            status: 'error',
            message: 'Impossible de nettoyer automatiquement',
            error: error.message,
            action: 'manual_restart_required'
        };
    }
}

/**
 * Obtenir un rapport d'état complet
 */
export function getComprehensiveStatus(socketInstance, stateManager) {
    const sessionInfo = getSessionsInfo();
    const expirationInfo = isSessionExpired();
    
    return {
        timestamp: new Date().toISOString(),
        service: {
            status: stateManager.isConnected ? 'connected' : 'disconnected',
            state: stateManager.state,
            uptime: stateManager.connectedAt ? Date.now() - stateManager.connectedAt : 0,
            errorCount: stateManager.errorCount || 0
        },
        session: {
            ...sessionInfo,
            expiration: expirationInfo
        },
        recommendation: generateRecommendation(stateManager, expirationInfo)
    };
}

/**
 * Générer une recommandation d'action
 */
function generateRecommendation(stateManager, expirationInfo) {
    if (expirationInfo.status === 'expired') {
        return {
            action: 'reset_session',
            severity: 'high',
            message: 'Session expirée - Réinitialisation recommandée'
        };
    }
    
    if (!stateManager.isConnected) {
        return {
            action: 'restart_service',
            severity: 'high',
            message: 'Service déconnecté - Redémarrage recommandé'
        };
    }
    
    return {
        action: 'no_action_needed',
        severity: 'low',
        message: 'Système opérationnel'
    };
}

export default {
    resetSessionAPI,
    deleteSessionForTenant,
    getSessionsInfo,
    isSessionExpired,
    cleanupTempFiles,
    handle405Error,
    getComprehensiveStatus
};
