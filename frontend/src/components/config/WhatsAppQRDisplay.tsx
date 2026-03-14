'use client';

import { useState, useEffect } from 'react';
import { apiCall } from '@/lib/api';

interface WhatsAppQR {
  tenant_id: number;
  status: 'awaiting_scan' | 'connected' | 'error';
  qr_code: string | null;
  phone: string | null;
  message: string;
}

export default function WhatsAppQRDisplay({ tenantId }: { tenantId: number }) {
  const [qrData, setQrData] = useState<WhatsAppQR | null>(null);
  const [loading, setLoading] = useState(false);
  const [phone, setPhone] = useState('');
  const [error, setError] = useState('');

  // fetchQRCode depends on tenantId and polling lifecycle for this component.
  useEffect(() => {
    fetchQRCode();
    // Poll every 5 seconds to check connection status
    const interval = setInterval(fetchQRCode, 5000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId]);

  const fetchQRCode = async () => {
    try {
      const response = await apiCall(`/api/tenants/${tenantId}/whatsapp/qr`);
      const data = await response.json();
      setQrData(data);
    } catch (err) {
      console.error('Error fetching QR code:', err);
    }
  };

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone) {
      setError('Veuillez entrer votre numéro WhatsApp');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await apiCall(`/api/tenants/${tenantId}/whatsapp/session`, {
        method: 'POST',
        body: JSON.stringify({ whatsapp_phone: phone }),
      });

      await response.json();
      setPhone('');
      fetchQRCode();
    } catch (err) {
      setError('❌ Erreur lors de la création de la session');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!qrData) {
    return <div className="text-center py-8">Chargement...</div>;
  }

  return (
    <div className="space-y-4">
      {/* Error State */}
      {qrData.status === 'error' && (
        <div className="bg-yellow-50 border border-yellow-200 p-6 rounded-lg text-center">
          <p className="text-yellow-800 mb-4">{qrData.message}</p>

          <form onSubmit={handleCreateSession} className="flex gap-2 max-w-sm mx-auto">
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="221780123456"
              className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded font-medium"
            >
              {loading ? 'Création...' : 'Connecter'}
            </button>
          </form>

          {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
        </div>
      )}

      {/* Connected State */}
      {qrData.status === 'connected' && (
        <div className="bg-green-50 border border-green-200 p-6 rounded-lg text-center">
          <div className="text-4xl mb-2">✅</div>
          <p className="text-green-800 font-medium">Connecté avec succès!</p>
          <p className="text-green-700 text-sm mt-1">{qrData.phone}</p>
          <p className="text-gray-600 text-xs mt-3">Votre bot WhatsApp est prêt à recevoir des messages</p>
        </div>
      )}

      {/* Awaiting Scan State */}
      {qrData.status === 'awaiting_scan' && (
        <div className="bg-blue-50 border border-blue-200 p-6 rounded-lg text-center">
          <div className="mb-4">
            <p className="text-blue-800 font-medium mb-2">📱 Scannez le QR code avec WhatsApp</p>
            <p className="text-blue-700 text-sm">{qrData.phone}</p>
          </div>

          {/* Placeholder for QR Code */}
          <div className="bg-white border-2 border-blue-300 p-8 rounded mx-auto w-64 h-64 flex items-center justify-center mb-4">
            <div className="text-center">
              <p className="text-gray-600 text-sm">📲 QR Code</p>
              <p className="text-gray-400 text-xs mt-2">(Intégration Baileys en cours)</p>
            </div>
          </div>

          <p className="text-blue-600 text-sm">
            💡 Attendez de voir ce code pour scanner avec WhatsApp
          </p>
        </div>
      )}
    </div>
  );
}
