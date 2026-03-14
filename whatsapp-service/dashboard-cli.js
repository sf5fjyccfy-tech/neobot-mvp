#!/usr/bin/env node

/**
 * 🎯 NéoBot WhatsApp - Professional Dashboard & Monitoring CLI
 * 
 * Real-time monitoring of WhatsApp service with:
 * - Live status updates
 * - Error tracking
 * - Performance metrics
 * - Log viewer
 * - Diagnostic tools
 * - Auto-alerts
 */

import axios from 'axios';
import chalk from 'chalk';
import blessed from 'blessed';

const SERVICE_URL = process.env.WHATSAPP_SERVICE_URL || 'http://localhost:3001';

class DashboardCLI {
    constructor() {
        this.screen = null;
        this.data = {
            metrics: null,
            logs: null,
            health: null,
            diagnosis: null
        };
        this.updateInterval = 1000; // 1 second
        this.lastChecked = null;
    }

    async initialize() {
        console.log(chalk.bold.blue('\n📊 Initializing NéoBot WhatsApp Dashboard...\n'));

        try {
            // Test connection
            const health = await axios.get(`${SERVICE_URL}/health`, { timeout: 5000 });
            console.log(chalk.green('✓') + ' Connected to WhatsApp service');
        } catch (err) {
            console.log(chalk.red('✗') + ' Cannot connect to service');
            console.log(chalk.yellow('Make sure the service is running: node whatsapp-service-v7-professional.js\n'));
            process.exit(1);
        }

        this.setupScreen();
        this.startMonitoring();
    }

    setupScreen() {
        this.screen = blessed.screen({
            mouse: true,
            keyboard: true,
            smartCSR: true,
            title: 'NéoBot WhatsApp Dashboard v7.0'
        });

        // Main layout panels
        this.createHeaderPanel();
        this.createStatusPanel();
        this.createMetricsPanel();
        this.createLogsPanel();
        this.createCommandFooter();

        this.screen.key(['escape', 'q', 'C-c'], () => {
            return process.exit(0);
        });

        this.screen.key(['r'], async () => {
            await this.refreshData();
        });

        this.screen.key(['d'], async () => {
            this.showDiagnostics();
        });

        this.screen.render();
    }

    createHeaderPanel() {
        blessed.box({
            parent: this.screen,
            top: 0,
            left: 0,
            width: '100%',
            height: 3,
            content: chalk.bold.cyan('🚀 NéoBot WhatsApp Service - Professional Dashboard\n') +
                    chalk.gray('Press [r] to refresh | [d] for diagnostics | [q] to quit'),
            style: {
                bg: 'blue',
                fg: 'white'
            }
        });
    }

    createStatusPanel() {
        this.statusBox = blessed.box({
            parent: this.screen,
            top: 3,
            left: 0,
            width: '50%',
            height: 12,
            border: 'line',
            title: ' Status ',
            content: 'Loading...',
            scrollable: true,
            mouse: true,
            keys: true
        });
    }

    createMetricsPanel() {
        this.metricsBox = blessed.box({
            parent: this.screen,
            top: 3,
            right: 0,
            width: '50%',
            height: 12,
            border: 'line',
            title: ' Metrics ',
            content: 'Loading...',
            scrollable: true,
            mouse: true,
            keys: true
        });
    }

    createLogsPanel() {
        this.logsBox = blessed.list({
            parent: this.screen,
            top: 15,
            left: 0,
            width: '100%',
            height: this.screen.height - 18,
            border: 'line',
            title: ' Recent Logs ',
            mouse: true,
            keys: true,
            autoScroll: true,
            scrollbar: {
                ch: ' ',
                track: {
                    bg: 'cyan'
                },
                style: {
                    bg: 'blue'
                }
            }
        });

        this.logsBox.on('select', (item) => {
            console.log(item);
        });
    }

    createCommandFooter() {
        blessed.box({
            parent: this.screen,
            bottom: 0,
            left: 0,
            width: '100%',
            height: 1,
            content: chalk.gray('[r] Refresh  [d] Diagnose  [q] Quit'),
            style: {
                bg: 'black',
                fg: 'gray'
            }
        });
    }

    async startMonitoring() {
        await this.refreshData();
        setInterval(() => this.refreshData(), this.updateInterval);
    }

    async refreshData() {
        try {
            const [metricsRes, logsRes, healthRes] = await Promise.all([
                axios.get(`${SERVICE_URL}/metrics`).catch(() => ({ data: null })),
                axios.get(`${SERVICE_URL}/logs?limit=30`).catch(() => ({ data: null })),
                axios.get(`${SERVICE_URL}/health/detailed`).catch(() => ({ data: null }))
            ]);

            this.data.metrics = metricsRes.data;
            this.data.logs = logsRes.data;
            this.data.health = healthRes.data;

            this.updateStatusPanel();
            this.updateMetricsPanel();
            this.updateLogsPanel();

            if (this.screen) {
                this.screen.render();
            }
        } catch (err) {
            // Silently fail if service unreachable
        }
    }

    updateStatusPanel() {
        let content = '';

        if (this.data.health) {
            const health = this.data.health;
            const statusColor = health.healthScore > 70 ? 'green' : health.healthScore > 40 ? 'yellow' : 'red';

            content += chalk.bold(this.getStatusIcon(health.status)) + ' ' + health.status.toUpperCase() + '\n';
            content += chalk.gray('Health Score: ') + chalk[statusColor](health.healthScore + '/100') + '\n\n';

            if (this.data.metrics) {
                const m = this.data.metrics;
                content += chalk.gray('Connection Status: ') + this.statusBadge(m.currentState) + '\n';
                content += chalk.gray('Total Connections: ') + m.connections + '\n';
                content += chalk.gray('Messages Processed: ') + m.messagesProcessed + '\n';
                content += chalk.gray('Success Rate: ') + chalk.green(m.successRate + '%') + '\n';
                content += chalk.gray('Uptime: ') + this.formatUptime(m.uptime) + '\n\n';

                content += chalk.gray('WebSocket Errors: ') + (m.websocketErrors > 0 ? chalk.red(m.websocketErrors) : chalk.green('0')) + '\n';
                content += chalk.gray('API Errors: ') + (m.apiErrors > 0 ? chalk.red(m.apiErrors) : chalk.green('0')) + '\n';

                if (m.lastErrorTime) {
                    content += chalk.gray('Last Error: ') +  chalk.yellow(this.formatTime(m.lastErrorTime)) + '\n';
                }
            }
        } else {
            content = chalk.red('⚠️  Unable to connect to service');
        }

        this.statusBox.setContent(content);
    }

    updateMetricsPanel() {
        let content = '';

        if (this.data.metrics) {
            const m = this.data.metrics;
            content += chalk.bold('📈 Performance\n');
            content += chalk.gray('Total Transactions: ') + (m.connections + m.messagesProcessed) + '\n';
            content += chalk.gray('Failed Transactions: ') + m.errorsEncountered + '\n';
            content += chalk.gray('QR Codes Generated: ') + m.qrCodesGenerated + '\n\n';

            content += chalk.bold('⏱️  Timing\n');
            content += chalk.gray('Current State: ') + this.colorizeState(m.currentState) + '\n';
            content += chalk.gray('Uptime: ') + this.formatUptime(m.uptime) + '\n\n';

            if (this.data.health && this.data.health.metrics) {
                const health = this.data.health.metrics;
                content += chalk.bold('📊 History\n');
                content += chalk.gray('Disconnections: ') + health.disconnections + '\n';
            }
        } else {
            content = chalk.red('Unable to load metrics');
        }

        this.metricsBox.setContent(content);
    }

    updateLogsPanel() {
        const logs = this.data.logs?.logs || [];
        
        const items = logs.map(log => {
            const icon = log.icon || '•';
            const levelColor = {
                'ERROR': 'red',
                'WARN': 'yellow',
                'INFO': 'cyan',
                'SUCCESS': 'green',
                'DEBUG': 'gray',
                'METRIC': 'magenta'
            }[log.level] || 'white';

            const timestamp = chalk.gray(log.timestamp.split('T')[1].slice(0, 8));
            const level = chalk[levelColor](`[${log.level}]`);
            const message = chalk.white(log.message);

            return `${timestamp} ${level} ${message}`;
        });

        this.logsBox.setItems(items);
    }

    async showDiagnostics() {
        this.screen.destroy();
        console.log(chalk.bold.cyan('\n🔍 Running System Diagnostics...\n'));

        try {
            const result = await axios.post(`${SERVICE_URL}/diagnose`, {});
            const diag = result.data;

            console.log(chalk.bold('📍 Network Check'));
            console.log('  Status: ' + (diag.checks.network.status === 'ok' ? chalk.green('✓') : chalk.red('✗')));
            console.log('  Message: ' + diag.checks.network.message);
            if (diag.checks.network.latency) {
                console.log('  Latency: ' + chalk.blue(diag.checks.network.latency + 'ms'));
            }

            console.log(chalk.bold('\n🔐 Auth State'));
            console.log('  Status: ' + diag.checks.authState.status);
            console.log('  Message: ' + diag.checks.authState.message);

            console.log(chalk.bold('\n⏱️  Timing Configuration'));
            console.log('  Connect Timeout: ' + chalk.blue(diag.checks.timing.connectTimeout + 'ms'));
            console.log('  Keep-Alive: ' + chalk.blue(diag.checks.timing.keepAliveInterval + 'ms'));
            console.log('  Query Timeout: ' + chalk.blue(diag.checks.timing.queryTimeout + 'ms'));

            console.log(chalk.bold('\n🌐 Browser Configuration'));
            console.log('  Available Browsers: ' + chalk.blue(diag.checks.browser.availableBrowsers));
            diag.checks.browser.browsers.forEach(b => {
                console.log('    • ' + chalk.gray(b));
            });

            console.log(chalk.bold('\n🖥️  WhatsApp Server Status'));
            console.log('  Status: ' + (diag.checks.whatsappStatus.status === 'ok' ? chalk.green('✓') : chalk.red('✗')));
            console.log('  Message: ' + diag.checks.whatsappStatus.message);
            if (diag.checks.whatsappStatus.latency) {
                console.log('  Latency: ' + chalk.blue(diag.checks.whatsappStatus.latency + 'ms'));
            }

            console.log(chalk.bold('\n✅ Diagnosis Complete\n'));
            console.log('Restarting dashboard in 3 seconds...\n');

            await new Promise(r => setTimeout(r, 3000));
            this.setupScreen();
            this.startMonitoring();

        } catch (err) {
            console.log(chalk.red('Error running diagnostics: ' + err.message + '\n'));
            process.exit(1);
        }
    }

    // Utilities
    statusBadge(state) {
        const colors = {
            'connected': 'green',
            'connecting': 'yellow',
            'disconnected': 'red',
            'error': 'red',
            'waiting_qr': 'blue',
            'initializing': 'gray'
        };

        const color = colors[state] || 'yellow';
        return chalk[color](state.toUpperCase());
    }

    colorizeState(state) {
        return this.statusBadge(state);
    }

    getStatusIcon(status) {
        return {
            'healthy': '🟢',
            'degraded': '🟡',
            'critical': '🔴'
        }[status] || '⚪';
    }

    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return chalk.green(`${hours}h ${minutes}m ${secs}s`);
        } else if (minutes > 0) {
            return chalk.green(`${minutes}m ${secs}s`);
        } else {
            return chalk.green(`${secs}s`);
        }
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }
}

// Start dashboard
const dashboard = new DashboardCLI();
dashboard.initialize().catch(err => {
    console.error('Error:', err);
    process.exit(1);
});
