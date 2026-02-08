import React from 'react';
import WhatsAppConnect from '../../components/whatsapp/WhatsAppConnect';

export default function Dashboard() {
  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🚀 Tableau de Bord NéoBot</h1>
        <p>Gérez votre assistant WhatsApp intelligent</p>
      </header>

      <div className="dashboard-content">
        <div className="widgets-grid">
          {/* Widget Connexion WhatsApp */}
          <div className="widget">
            <div className="widget-header">
              <h2>Connexion WhatsApp</h2>
            </div>
            <div className="widget-content">
              <WhatsAppConnect />
            </div>
          </div>

          {/* Widget Statistiques */}
          <div className="widget">
            <div className="widget-header">
              <h2>📊 Statistiques</h2>
            </div>
            <div className="widget-content">
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-number">0</div>
                  <div className="stat-label">Messages aujourd'hui</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number">0</div>
                  <div className="stat-label">Conversations actives</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number">0%</div>
                  <div className="stat-label">Taux de réponse</div>
                </div>
              </div>
            </div>
          </div>

          {/* Widget Actions Rapides */}
          <div className="widget">
            <div className="widget-header">
              <h2>⚡ Actions Rapides</h2>
            </div>
            <div className="widget-content">
              <div className="quick-actions">
                <button className="action-btn">📋 Voir les conversations</button>
                <button className="action-btn">⚙️ Configurer le bot</button>
                <button className="action-btn">📈 Voir les analytics</button>
                <button className="action-btn">🔔 Paramètres notifications</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .dashboard {
          min-height: 100vh;
          background: #f8f9fa;
          padding: 20px;
        }
        
        .dashboard-header {
          text-align: center;
          margin-bottom: 30px;
        }
        
        .dashboard-header h1 {
          color: #333;
          margin: 0;
          font-size: 2.5rem;
        }
        
        .dashboard-header p {
          color: #666;
          font-size: 1.1rem;
          margin: 8px 0 0 0;
        }
        
        .widgets-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 24px;
          max-width: 1200px;
          margin: 0 auto;
        }
        
        @media (min-width: 768px) {
          .widgets-grid {
            grid-template-columns: 1fr 1fr;
          }
        }
        
        @media (min-width: 1024px) {
          .widgets-grid {
            grid-template-columns: 2fr 1fr 1fr;
          }
        }
        
        .widget {
          background: white;
          border-radius: 12px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
          overflow: hidden;
        }
        
        .widget-header {
          background: #007bff;
          color: white;
          padding: 16px 20px;
        }
        
        .widget-header h2 {
          margin: 0;
          font-size: 1.2rem;
        }
        
        .widget-content {
          padding: 20px;
        }
        
        .stats-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 12px;
        }
        
        .stat-card {
          text-align: center;
          padding: 16px;
          background: #f8f9fa;
          border-radius: 8px;
          border: 1px solid #e9ecef;
        }
        
        .stat-number {
          font-size: 2rem;
          font-weight: bold;
          color: #007bff;
          margin-bottom: 4px;
        }
        
        .stat-label {
          font-size: 0.9rem;
          color: #666;
        }
        
        .quick-actions {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        
        .action-btn {
          padding: 12px 16px;
          background: #f8f9fa;
          border: 1px solid #dee2e6;
          border-radius: 6px;
          cursor: pointer;
          text-align: left;
          font-size: 14px;
          transition: all 0.2s;
        }
        
        .action-btn:hover {
          background: #e9ecef;
          border-color: #007bff;
        }
      `}</style>
    </div>
  );
}
