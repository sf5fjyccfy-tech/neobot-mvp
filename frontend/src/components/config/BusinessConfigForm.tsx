'use client';

import { useState, useEffect } from 'react';
import { apiCall } from '@/lib/api';

interface Product {
  id?: string;
  name: string;
  price: number;
  description: string;
  category?: string;
}

interface BusinessConfigData {
  business_type: string;
  company_name: string;
  company_description: string;
  tone: string;
  selling_focus: string;
  // Restaurant specific
  menu_items?: Product[];
  hours?: string;
  delivery?: boolean;
  delivery_zones?: string;
  reservations?: boolean;
  // Ecommerce specific
  products?: Product[];
  return_policy?: string;
  warranty_info?: string;
}

const BUSINESS_TYPES = [
  { value: 'restaurant', label: 'Restaurant' },
  { value: 'ecommerce', label: 'E-commerce' },
  { value: 'travel', label: 'Voyage & Tourisme' },
  { value: 'salon', label: 'Salon & Beauté' },
  { value: 'fitness', label: 'Fitness & Gym' },
  { value: 'consulting', label: 'Consulting' },
  { value: 'custom', label: 'Autre' },
];

const TONES = ['Professional', 'Friendly', 'Expert', 'Casual', 'Formal'];

export default function BusinessConfigForm({ tenantId }: { tenantId: number }) {
  const [config, setConfig] = useState<BusinessConfigData>({
    business_type: 'restaurant',
    company_name: '',
    company_description: '',
    tone: 'Friendly',
    selling_focus: '',
    menu_items: [],
    products: [],
    hours: '',
    delivery: false,
    delivery_zones: '',
    reservations: false,
    return_policy: '',
    warranty_info: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // loadConfig depends on tenantId and should rerun when tenant changes.
  useEffect(() => {
    loadConfig();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId]);

  const loadConfig = async () => {
    try {
      const response = await apiCall(`/api/tenants/${tenantId}/business/config`);
      const data = await response.json();
      setConfig(prev => ({ ...prev, ...data }));
    } catch (err) {
      console.log('No existing config found (first time)');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setConfig(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  const handleProductAdd = () => {
    const items = config.business_type === 'restaurant' ? 'menu_items' : 'products';
    setConfig(prev => ({
      ...prev,
      [items]: [...(prev[items as keyof BusinessConfigData] as Product[] || []), 
        { name: '', price: 0, description: '' }
      ]
    }));
  };

  const handleProductChange = (index: number, field: string, value: any) => {
    const items = config.business_type === 'restaurant' ? 'menu_items' : 'products';
    const products = [...((config[items as keyof BusinessConfigData] as Product[]) || [])];
    products[index] = { ...products[index], [field]: value };
    setConfig(prev => ({ ...prev, [items]: products }));
  };

  const handleProductRemove = (index: number) => {
    const items = config.business_type === 'restaurant' ? 'menu_items' : 'products';
    setConfig(prev => ({
      ...prev,
      [items]: (prev[items as keyof BusinessConfigData] as Product[] || []).filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await apiCall(`/api/tenants/${tenantId}/business/config`, {
        method: 'POST',
        body: JSON.stringify(config),
      });

      await response.json();
      setSuccess('✅ Configuration sauvegardée avec succès!');
      
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('❌ Erreur lors de la sauvegarde');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const items = config.business_type === 'restaurant' ? config.menu_items : config.products;

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
          {success}
        </div>
      )}

      {/* Business Type Selection */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Type d'entreprise
          </label>
          <select
            name="business_type"
            aria-label="Type d'entreprise"
            value={config.business_type}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {BUSINESS_TYPES.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Ton de voix
          </label>
          <select
            name="tone"
            aria-label="Ton de voix"
            value={config.tone}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {TONES.map(tone => (
              <option key={tone} value={tone}>
                {tone}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Company Info */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Nom de l'entreprise
        </label>
        <input
          type="text"
          name="company_name"
          value={config.company_name}
          onChange={handleChange}
          placeholder="La Saveur Restaurant"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          name="company_description"
          value={config.company_description}
          onChange={handleChange}
          placeholder="Restaurant authentique avec les meilleures pizzas..."
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Focus commercial
        </label>
        <input
          type="text"
          name="selling_focus"
          value={config.selling_focus}
          onChange={handleChange}
          placeholder="Qualité, Service, Prix"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Restaurant Specific */}
      {config.business_type === 'restaurant' && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Horaires d'ouverture
            </label>
            <input
              type="text"
              name="hours"
              value={config.hours}
              onChange={handleChange}
              placeholder="Lun-Ven: 11h-22h, Sam-Dim: 12h-23h"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="delivery"
                checked={config.delivery}
                onChange={handleChange}
                className="rounded"
              />
              <span className="text-sm font-medium text-gray-700">Livraison disponible</span>
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="reservations"
                checked={config.reservations}
                onChange={handleChange}
                className="rounded"
              />
              <span className="text-sm font-medium text-gray-700">Réservations</span>
            </label>
          </div>

          {config.delivery && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Zones de livraison
              </label>
              <input
                type="text"
                name="delivery_zones"
                value={config.delivery_zones}
                onChange={handleChange}
                placeholder="Dakar, Banlieue"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}
        </>
      )}

      {/* Products/Menu Items */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-gray-700">
            {config.business_type === 'restaurant' ? 'Menu' : 'Produits'}
          </label>
          <button
            type="button"
            onClick={handleProductAdd}
            className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
          >
            + Ajouter
          </button>
        </div>

        <div className="space-y-2 max-h-96 overflow-y-auto">
          {items && items.map((item, index) => (
            <div key={index} className="flex gap-2 p-2 bg-gray-50 rounded">
              <input
                type="text"
                placeholder="Nom"
                value={item.name}
                onChange={(e) => handleProductChange(index, 'name', e.target.value)}
                className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
              />
              <input
                type="number"
                placeholder="Prix"
                value={item.price}
                onChange={(e) => handleProductChange(index, 'price', parseFloat(e.target.value))}
                className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
              />
              <input
                type="text"
                placeholder="Description"
                value={item.description}
                onChange={(e) => handleProductChange(index, 'description', e.target.value)}
                className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
              />
              <button
                type="button"
                onClick={() => handleProductRemove(index)}
                className="px-2 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* E-commerce Specific */}
      {config.business_type === 'ecommerce' && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Politique de retour
            </label>
            <textarea
              name="return_policy"
              value={config.return_policy}
              onChange={handleChange}
              placeholder="30 jours pour retourner les articles..."
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Information de garantie
            </label>
            <textarea
              name="warranty_info"
              value={config.warranty_info}
              onChange={handleChange}
              placeholder="1 an de garantie sur tous les produits..."
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-md transition"
      >
        {loading ? 'Sauvegarde en cours...' : '💾 Sauvegarder la configuration'}
      </button>
    </form>
  );
}
