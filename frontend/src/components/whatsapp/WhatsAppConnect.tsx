'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import { buildApiUrl } from '@/lib/api';

interface WhatsAppStatus {
  connected: boolean;
  qr_code: string | null;
  status: string;
}

const WhatsAppConnect: React.FC = () => {
  const [status, setStatus] = useState<WhatsAppStatus>({
    connected: false,
    qr_code: null,
    status: 'disconnected'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Polling callback intentionally remains stable for mount lifecycle.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    fetchWhatsAppStatus();
    
    // Polling pour les mises à jour (plus simple que WebSocket)
    const interval = setInterval(fetchWhatsAppStatus, 3000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchWhatsAppStatus = async () => {
    try {
      const response = await fetch(buildApiUrl('/api/whatsapp/status'));
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
        setError(null);
      }
      setLoading(false);
    } catch {
      setError('Impossible de se connecter au serveur');
      setLoading(false);
    }
  };

  const restartConnection = async () => {
    try {
      setLoading(true);
      await fetch(buildApiUrl('/api/whatsapp/restart'), { 
        method: 'POST' 
      });
      // Attendre un peu puis rafraîchir le statut
      setTimeout(fetchWhatsAppStatus, 2000);
    } catch {
      setError('Erreur lors du redémarrage');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="whatsapp-connect loading">
        <div className="spinner"></div>
        <p>Chargement du statut WhatsApp...</p>
      </div>
    );
  }

  return (
    <div className="whatsapp-connect">
      <h2>🔗 Connexion WhatsApp</h2>
      
      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}
      
      <div className={`status ${status.connected ? 'connected' : 'disconnected'}`}>
        {status.connected ? (
          <>
            <span className="status-icon">✅</span>
            <span>WhatsApp connecté</span>
          </>
        ) : (
          <>
            <span className="status-icon">❌</span>
            <span>WhatsApp déconnecté</span>
          </>
        )}
      </div>

      {status.qr_code && !status.connected && (
        <div className="qr-section">
          <p className="qr-title">📱 Scannez ce QR code avec WhatsApp</p>
          <div className="qr-code">
            <Image
              src={`data:image/png;base64,${status.qr_code}`}
              alt="QR Code WhatsApp"
              width={250}
              height={250}
              unoptimized
            />
          </div>
          <div className="instructions">
            <h4>Instructions :</h4>
            <ol>
              <li>Ouvrez <strong>WhatsApp</strong> sur votre téléphone</li>
              <li>Allez dans <strong>Paramètres</strong> → <strong>Appareils connectés</strong></li>
              <li>Tapotez sur <strong>Lier un appareil</strong></li>
              <li>Scannez le code QR ci-dessus</li>
            </ol>
          </div>
        </div>
      )}

      <div className="actions">
        <button 
          onClick={restartConnection} 
          disabled={loading}
          className="restart-btn"
        >
          {loading ? '🔄 Redémarrage...' : '🔄 Redémarrer la connexion'}
        </button>
        
        <button 
          onClick={fetchWhatsAppStatus}
          className="refresh-btn"
        >
          🔄 Actualiser
        </button>
      </div>

      <style jsx>{`
        .whatsapp-connect {
          background: white;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
          max-width: 500px;
          margin: 20px auto;
        }
        
        .loading {
          text-align: center;
          padding: 40px;
        }
        
        .spinner {
          border: 4px solid #f3f3f3;
          border-top: 4px solid #007bff;
          border-radius: 50%;
          width: 40px;
          height: 40px;
          animation: spin 1s linear infinite;
          margin: 0 auto 16px;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        h2 {
          margin: 0 0 20px 0;
          color: #333;
          text-align: center;
        }
        
        .error-message {
          background: #f8d7da;
          color: #721c24;
          padding: 12px;
          border-radius: 6px;
          margin-bottom: 16px;
          text-align: center;
        }
        
        .status {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 20px;
          font-weight: 600;
        }
        
        .connected {
          background: #d4edda;
          color: #155724;
          border: 1px solid #c3e6cb;
        }
        
        .disconnected {
          background: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
        }
        
        .status-icon {
          font-size: 18px;
        }
        
        .qr-section {
          text-align: center;
          margin: 20px 0;
        }
        
        .qr-title {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 16px;
          color: #333;
        }
        
        .qr-code {
          background: white;
          padding: 20px;
          border-radius: 8px;
          border: 2px solid #e9ecef;
          display: inline-block;
          margin-bottom: 16px;
        }
        
        .qr-code img {
          max-width: 250px;
          height: auto;
        }
        
        .instructions {
          text-align: left;
          background: #f8f9fa;
          padding: 16px;
          border-radius: 8px;
          border-left: 4px solid #007bff;
        }
        
        .instructions h4 {
          margin: 0 0 12px 0;
          color: #333;
        }
        
        .instructions ol {
          margin: 0;
          padding-left: 20px;
        }
        
        .instructions li {
          margin-bottom: 8px;
          color: #555;
        }
        
        .actions {
          display: flex;
          gap: 12px;
          justify-content: center;
          margin-top: 20px;
        }
        
        .restart-btn, .refresh-btn {
          padding: 10px 16px;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 600;
          transition: all 0.2s;
        }
        
        .restart-btn {
          background: #007bff;
          color: white;
        }
        
        .restart-btn:hover:not(:disabled) {
          background: #0056b3;
        }
        
        .restart-btn:disabled {
          background: #6c757d;
          cursor: not-allowed;
        }
        
        .refresh-btn {
          background: #6c757d;
          color: white;
        }
        
        .refresh-btn:hover {
          background: #545b62;
        }
      `}</style>
    </div>
  );
};

export default WhatsAppConnect;
