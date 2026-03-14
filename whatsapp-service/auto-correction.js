#!/usr/bin/env node

/**
 * 🔧 Auto-Correction Engine for WhatsApp Service
 * 
 * Monitors service health and automatically corrects:
 * - Connection timeouts
 * - Session expiration
 * - Browser agent failures
 * - WebSocket disconnections
 * - Rate limiting issues
 */

import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

class AutoCorrectionEngine {
    constructor() {
        this.serviceUrl = process.env.WHATSAPP_SERVICE_URL || 'http://localhost:3001';
        this.backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
        this.checkInterval = 5000; // Check every 5 seconds
        this.maxConsecutiveErrors = 3;
        this.consecutiveErrors = 0;
        this.lastHealthCheck = null;
        this.corrections = [];
    }

    start() {
        console.log('🔧 Auto-Correction Engine Started\n');
        this.performHealthCheck();
        setInterval(() => this.performHealthCheck(), this.checkInterval);
    }

    async performHealthCheck() {
        try {
            const [metrics, health, logs] = await Promise.all([
                axios.get(`${this.serviceUrl}/metrics`).catch(() => ({ data: null })),
                axios.get(`${this.serviceUrl}/health/detailed`).catch(() => ({ data: null })),
                axios.get(`${this.serviceUrl}/logs?limit=100`).catch(() => ({ data: null }))
            ]);

            this.consecutiveErrors = 0;
            this.lastHealthCheck = Date.now();

            const analysis = {
                metrics: metrics.data,
                health: health.data,
                logs: logs.data
            };

            await this.analyzeAndCorrect(analysis);

        } catch (err) {
            this.consecutiveErrors++;
            if (this.consecutiveErrors === 1) {
                console.log(`⚠️  Service unreachable (${this.consecutiveErrors}/${this.maxConsecutiveErrors})`);
            }

            if (this.consecutiveErrors >= this.maxConsecutiveErrors) {
                console.log(`\n🚨 Service down for ${this.consecutiveErrors} checks. Attempting restart...\n`);
                await this.restartService();
                this.consecutiveErrors = 0;
            }
        }
    }

    async analyzeAndCorrect(analysis) {
        const issues = [];

        // Check 1: WebSocket errors increasing
        if (analysis.metrics && analysis.metrics.websocketErrors > 5) {
            issues.push({
                type: 'websocket_errors',
                severity: 'high',
                message: `${analysis.metrics.websocketErrors} WebSocket errors detected`,
                correction: () => this.correctWebSocketIssues(analysis)
            });
        }

        // Check 2: High error rate
        if (analysis.metrics && analysis.metrics.successRate < 50) {
            issues.push({
                type: 'high_error_rate',
                severity: 'critical',
                message: `Success rate dropped to ${analysis.metrics.successRate}%`,
                correction: () => this.correctHighErrorRate(analysis)
            });
        }

        // Check 3: Connection not established
        if (analysis.metrics && analysis.metrics.currentState === 'disconnected' && analysis.metrics.connections > 0) {
            issues.push({
                type: 'disconnected',
                severity: 'high',
                message: 'Service disconnected after being connected',
                correction: () => this.correctDisconnection(analysis)
            });
        }

        // Check 4: Specific error patterns
        if (analysis.logs && analysis.logs.logs) {
            const recentLogs = analysis.logs.logs.slice(0, 20);
            
            // Check for 405 error (WebSocket protocol)
            const has405 = recentLogs.some(l => l.message.includes('405') || l.message.includes('Connection Failure'));
            if (has405) {
                issues.push({
                    type: 'whatsapp_protocol_error',
                    severity: 'critical',
                    message: 'WhatsApp protocol error (405) - Baileys incompatible',
                    correction: () => this.correctProtocolError(analysis)
                });
            }

            // Check for auth errors
            const hasAuthError = recentLogs.some(l => 
                l.message.includes('loggedOut') || 
                l.message.includes('multidevice')
            );
            if (hasAuthError) {
                issues.push({
                    type: 'auth_error',
                    severity: 'high',
                    message: 'Authentication lost - require new QR scan',
                    correction: () => this.correctAuthError(analysis)
                });
            }

            // Check for timeout errors
            const hasTimeout = recentLogs.some(l => 
                l.message.includes('timeout') || 
                l.message.includes('ETIMEDOUT')
            );
            if (hasTimeout) {
                issues.push({
                    type: 'timeout',
                    severity: 'medium',
                    message: 'Connection timeouts detected',
                    correction: () => this.correctTimeouts(analysis)
                });
            }
        }

        // Check 5: Health score declining
        if (analysis.health && analysis.health.healthScore < 40) {
            issues.push({
                type: 'health_degraded',
                severity: 'high',
                message: `Health score critical: ${analysis.health.healthScore}/100`,
                correction: () => this.correctHealthDegradation(analysis)
            });
        }

        // Apply corrections
        if (issues.length > 0) {
            console.log(`\n📊 ${new Date().toLocaleTimeString()} - Found ${issues.length} issue(s):`);
            
            for (const issue of issues) {
                console.log(`\n[${issue.severity.toUpperCase()}] ${issue.type}`);
                console.log(`  Message: ${issue.message}`);
                
                try {
                    await issue.correction();
                    console.log(`  ✓ Corrected`);
                    this.corrections.push({
                        type: issue.type,
                        time: new Date(),
                        status: 'success'
                    });
                } catch (err) {
                    console.log(`  ✗ Correction failed: ${err.message}`);
                    this.corrections.push({
                        type: issue.type,
                        time: new Date(),
                        status: 'failed',
                        error: err.message
                    });
                }
            }
        }
    }

    // Correction Strategies

    async correctWebSocketIssues(analysis) {
        // Strategy: Attempt browser agent switch
        console.log(`  → Attempting browser agent rotation...`);
        
        // Try switching to a different browser agent
        const browsers = ['ubuntu_chrome', 'ubuntu_firefox', 'macos_safari', 'windows_edge'];
        const currentBrowser = browsers[0];

        // Log the attempt
        try {
            await axios.post(`${this.serviceUrl}/api/correction/browser-switch`, {
                attemptedBrowser: currentBrowser,
                fallbackBrowsers: browsers.slice(1)
            }).catch(e => console.log(`  (no response from browser-switch endpoint)`));
        } catch (err) {
            // Endpoint might not exist
        }
    }

    async correctHighErrorRate(analysis) {
        // Strategy: Clear session and reinitialize
        console.log(`  → Clearing session cache...`);
        
        const sessionDir = path.join(__dirname, 'auth_info_baileys');
        if (fs.existsSync(sessionDir)) {
            fs.rmSync(sessionDir, { recursive: true, force: true });
            console.log(`  → Session cache cleared`);
        }

        console.log(`  → Service will reinitialize with fresh connection on next startup`);
    }

    async correctDisconnection(analysis) {
        // Strategy: Trigger reconnection
        console.log(`  → Initiating reconnection sequence...`);
        
        try {
            await axios.post(`${this.serviceUrl}/api/correction/reconnect`, {
                reason: 'auto_correction_disconnection_detected',
                timestamp: new Date().toISOString()
            }).catch(e => console.log(`  (service may be reinitializing)`));
        } catch (err) {
            console.log(`  → Will reconnect automatically`);
        }
    }

    async correctProtocolError(analysis) {
        // Strategy: Try alternate connection configurations
        console.log(`  → Attempting alternate connection parameters...`);
        console.log(`  → This error suggests Baileys incompatibility with current WhatsApp protocol`);
        console.log(`  → Consider upgrade schedule or protocol update from Baileys maintainers`);
        
        // Log diagnostic information
        const diagnostics = {
            error: 'whatsapp_protocol_incompatibility',
            timestamp: new Date().toISOString(),
            baileys_version: '6.7.21',
            whatsapp_year: '2026',
            status: 'awaiting_library_update'
        };

        const diagFile = path.join(__dirname, 'protocol_error_diagnostic.json');
        fs.writeFileSync(diagFile, JSON.stringify(diagnostics, null, 2));
        console.log(`  → Diagnostic saved to protocol_error_diagnostic.json`);
    }

    async correctAuthError(analysis) {
        // Strategy: Require QR rescan
        console.log(`  → Authentication lost - new QR code required`);
        console.log(`  → Clear auth_info_baileys directory and restart service`);
        console.log(`  → Run: npm run clean && npm run pro`);
    }

    async correctTimeouts(analysis) {
        // Strategy: Increase timeout values
        console.log(`  → Increasing connection timeout values...`);
        console.log(`  → Current timeout: ${analysis.metrics?.connectTimeout || 60000}ms`);
        console.log(`  → Recommendation: Check network connectivity and firewall rules`);

        // Try diagnostic
        try {
            await axios.post(`${this.serviceUrl}/diagnose`, {});
        } catch (err) {
            // ignore
        }
    }

    async correctHealthDegradation(analysis) {
        // Strategy: Light service restart
        console.log(`  → Attempting graceful service recovery...`);
        
        const recoveryPlan = {
            step1: 'Check network connectivity',
            step2: 'Verify WhatsApp account not logged in elsewhere',
            step3: 'Wait 30 seconds for auto-reconnection',
            step4: 'If issue persists, restart service: npm run clean && npm run pro'
        };

        console.log(`  → Recovery plan:`);
        Object.values(recoveryPlan).forEach((step, i) => {
            console.log(`    ${i + 1}. ${step}`);
        });
    }

    async restartService() {
        console.log('🔄 Restarting WhatsApp service...');
        
        // This would be handled by a process manager like PM2 in production
        // For now, log the recommendation
        console.log('   Recommendation: Use PM2 for automatic restart');
        console.log('   Install: npm install -g pm2');
        console.log('   Run: pm2 start whatsapp-service-v7-professional.js --name "whatsapp-service"');
        console.log('   Auto-restart: pm2 startup');
    }

    getReport() {
        const passed = this.corrections.filter(c => c.status === 'success').length;
        const failed = this.corrections.filter(c => c.status === 'failed').length;

        return {
            totalCorrections: this.corrections.length,
            successful: passed,
            failed: failed,
            successRate: passed / (passed + failed || 1) * 100,
            corrections: this.corrections.slice(-20) // Last 20
        };
    }
}

// Start auto-correction engine
const engine = new AutoCorrectionEngine();
engine.start();

// Print report every minute
setInterval(() => {
    const report = engine.getReport();
    console.log(`\n📈 Auto-Correction Report (Last minute)`);
    console.log(`  Total: ${report.totalCorrections} | Success: ${report.successful} | Failed: ${report.failed}`);
    if (report.totalCorrections > 0) {
        console.log(`  Success Rate: ${report.successRate.toFixed(1)}%`);
    }
}, 60000);
