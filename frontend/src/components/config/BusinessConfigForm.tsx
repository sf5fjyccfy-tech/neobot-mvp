'use client';

import { useState, useEffect } from 'react';
import { apiCall, getBusinessInfo } from '@/lib/api';

interface ProductServiceItem {
  name: string;
  price: number;
  description: string;
  category?: string;
  image_url?: string; // base64 — envoyé par le bot si le client demande ce produit
}

interface BusinessConfigData {
  business_type_slug: string;
  company_name: string;
  company_description: string;
  tone: string;
  selling_focus: string;
  products_services: ProductServiceItem[];
  // extras stockés dans company_description si besoin
  hours?: string;
  delivery?: boolean;
  delivery_zones?: string;
  reservations?: boolean;
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

const TONES = [
  { value: 'Professional', label: 'Professionnel' },
  { value: 'Friendly', label: 'Amical' },
  { value: 'Expert', label: 'Expert' },
  { value: 'Casual', label: 'Décontracté' },
  { value: 'Formal', label: 'Formel' },
];

export default function BusinessConfigForm({ tenantId }: { tenantId: number }) {
  // État initial vide — identique serveur & client (évite le mismatch d'hydratation)
  const [config, setConfig] = useState<BusinessConfigData>({
    business_type_slug: 'restaurant',
    company_name: '',
    company_description: '',
    tone: 'Friendly',
    selling_focus: '',
    products_services: [],
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
  const [rawActivity, setRawActivity] = useState('');
  const [genLoading, setGenLoading] = useState(false);

  useEffect(() => {
    // Pré-remplir depuis localStorage uniquement côté client, après hydratation
    const savedInfo = getBusinessInfo();
    if (savedInfo) {
      setConfig(prev => ({
        ...prev,
        business_type_slug: savedInfo.business_type || prev.business_type_slug,
        company_name: savedInfo.tenant_name || prev.company_name,
      }));
    }
    loadConfig();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId]);

  const loadConfig = async () => {
    try {
      const response = await apiCall(`/api/tenants/${tenantId}/business/config`);
      const data = await response.json();
      if (data.status === 'not_configured') return;
      // Le backend retourne business_type (slug), on le mappe en business_type_slug
      setConfig(prev => ({
        ...prev,
        business_type_slug: data.business_type || prev.business_type_slug,
        company_name: data.company_name || prev.company_name,
        company_description: data.company_description || '',
        tone: data.tone || 'Friendly',
        selling_focus: data.selling_focus || '',
        products_services: data.products_services || [],
      }));
    } catch {
      // Pas de config existante — état initial conservé
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
    setConfig(prev => ({
      ...prev,
      products_services: [...prev.products_services, { name: '', price: 0, description: '', image_url: '' }],
    }));
  };

  const handleProductChange = (index: number, field: string, value: string | number) => {
    const updated = [...config.products_services];
    updated[index] = { ...updated[index], [field]: value };
    setConfig(prev => ({ ...prev, products_services: updated }));
  };

  const handleProductRemove = (index: number) => {
    setConfig(prev => ({
      ...prev,
      products_services: prev.products_services.filter((_, i) => i !== index),
    }));
  };

  const handleProductImage = (index: number, file: File) => {
    if (file.size > 500 * 1024) {
      alert('Image trop lourde — maximum 500 Ko.');
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      handleProductChange(index, 'image_url', e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleGenerateDescription = async () => {
    if (!rawActivity.trim()) return;
    setGenLoading(true);
    try {
      const res = await apiCall(`/api/tenants/${tenantId}/business/generate-description`, {
        method: 'POST',
        body: JSON.stringify({
          raw_activity: rawActivity,
          company_name: config.company_name,
          business_type: config.business_type_slug,
        }),
      });
      const data = await res.json();
      if (data.description) {
        setConfig(prev => ({ ...prev, company_description: data.description }));
      }
    } catch {
      // silencieux — le champ description reste modifiable manuellement
    } finally {
      setGenLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    // Construction de la description enrichie avec les extras
    let fullDescription = config.company_description || '';
    if (config.business_type_slug === 'restaurant') {
      if (config.hours) fullDescription += `\n\nHoraires : ${config.hours}`;
      if (config.delivery) fullDescription += `\nLivraison disponible${config.delivery_zones ? ` — Zones : ${config.delivery_zones}` : ''}`;
      if (config.reservations) fullDescription += '\nRéservations acceptées';
    }
    if (config.business_type_slug === 'ecommerce') {
      if (config.return_policy) fullDescription += `\n\nPolitique de retour : ${config.return_policy}`;
      if (config.warranty_info) fullDescription += `\nGarantie : ${config.warranty_info}`;
    }

    try {
      const payload = {
        business_type_slug: config.business_type_slug,
        company_name: config.company_name,
        company_description: fullDescription.trim(),
        tone: config.tone,
        selling_focus: config.selling_focus,
        products_services: config.products_services,
      };

      await apiCall(`/api/tenants/${tenantId}/business/config`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setSuccess('✅ Configuration sauvegardée avec succès !');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Vérifiez les champs';
      setError(`❌ Erreur lors de la sauvegarde : ${msg}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const NEON = '#FF4D00';
  const BG = '#06040E';
  const SURFACE = '#0C0916';
  const BORDER = '#1C1428';
  const MUTED = '#5C4E7A';
  const TEXT = '#E0E0FF';

  const fieldStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px 14px',
    background: BG,
    border: `1px solid ${BORDER}`,
    borderRadius: 8,
    color: TEXT,
    fontSize: 13,
    outline: 'none',
    boxSizing: 'border-box',
    fontFamily: '"DM Sans", sans-serif',
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    fontSize: 12,
    color: MUTED,
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    fontWeight: 600,
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {error && (
        <div style={{ background: '#FF444415', border: '1px solid #FF444440', color: '#FF8888', padding: '10px 16px', borderRadius: 8, fontSize: 13 }}>
          {error}
        </div>
      )}

      {success && (
        <div style={{ background: `${NEON}15`, border: `1px solid ${NEON}40`, color: NEON, padding: '10px 16px', borderRadius: 8, fontSize: 13 }}>
          {success}
        </div>
      )}

      {/* Business Type Selection */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div>
          <label style={labelStyle}>Type d'entreprise</label>
          <select name="business_type_slug" aria-label="Type d'entreprise" value={config.business_type_slug} onChange={handleChange} style={fieldStyle}>
            {BUSINESS_TYPES.map(type => (
              <option key={type.value} value={type.value}>{type.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label style={labelStyle}>Ton de voix</label>
          <select name="tone" aria-label="Ton de voix" value={config.tone} onChange={handleChange} style={fieldStyle}>
            {TONES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Company Info */}
      <div>
        <label style={labelStyle}>Nom de l'entreprise</label>
        <input type="text" name="company_name" value={config.company_name} onChange={handleChange} placeholder="La Saveur Restaurant" style={fieldStyle} />
      </div>
      <div>
        <label style={labelStyle}>Description de votre agent</label>
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <input
            type="text"
            value={rawActivity}
            onChange={e => setRawActivity(e.target.value)}
            placeholder="Ex : je vends des chaussures de sport à Douala, principalement en ligne"
            style={{ ...fieldStyle, flex: 1 }}
          />
          <button
            type="button"
            onClick={handleGenerateDescription}
            disabled={genLoading || !rawActivity.trim()}
            style={{
              padding: '10px 14px',
              background: genLoading || !rawActivity.trim() ? `${NEON}10` : `${NEON}20`,
              border: `1px solid ${genLoading || !rawActivity.trim() ? `${NEON}15` : `${NEON}50`}`,
              borderRadius: 8, color: genLoading || !rawActivity.trim() ? MUTED : NEON,
              fontSize: 12, fontWeight: 700, cursor: genLoading || !rawActivity.trim() ? 'not-allowed' : 'pointer',
              whiteSpace: 'nowrap' as const,
            }}
          >
            {genLoading ? '⏳...' : '✨ Générer'}
          </button>
        </div>
        <p style={{ color: MUTED, fontSize: 11, margin: '0 0 6px' }}>Décrivez votre activité en quelques mots, l&apos;IA génère la description — vous pouvez la modifier ensuite</p>
        <textarea name="company_description" value={config.company_description} onChange={handleChange} placeholder="Description générée automatiquement ou saisissez la vôtre..." rows={3} maxLength={1000} style={{ ...fieldStyle, resize: 'vertical' as const }} />
      </div>
      <div>
        <label style={labelStyle}>Vos points forts</label>
        <input type="text" name="selling_focus" value={config.selling_focus} onChange={handleChange} placeholder="Livraison rapide, produits 100% locaux, service 7j/7" style={fieldStyle} />
        <p style={{ color: MUTED, fontSize: 11, margin: '4px 0 0' }}>Ce que votre bot mettra en avant dans ses réponses</p>
      </div>

      {/* Restaurant Specific */}
      {config.business_type_slug === 'restaurant' && (
        <>
          <div>
            <label style={labelStyle}>Horaires d'ouverture</label>
            <input type="text" name="hours" value={config.hours} onChange={handleChange} placeholder="Lun-Ven: 11h-22h, Sam-Dim: 12h-23h" style={fieldStyle} />
          </div>
          <div style={{ display: 'flex', gap: 20 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
              <input type="checkbox" name="delivery" checked={config.delivery} onChange={handleChange} />
              <span style={{ color: TEXT, fontSize: 13 }}>Livraison disponible</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
              <input type="checkbox" name="reservations" checked={config.reservations} onChange={handleChange} />
              <span style={{ color: TEXT, fontSize: 13 }}>Réservations</span>
            </label>
          </div>
          {config.delivery && (
            <div>
              <label style={labelStyle}>Zones de livraison</label>
              <input type="text" name="delivery_zones" value={config.delivery_zones} onChange={handleChange} placeholder="Douala, Yaoundé" style={fieldStyle} />
            </div>
          )}
        </>
      )}

      {/* Products/Menu Items */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <label style={labelStyle}>
            {config.business_type_slug === 'restaurant' ? 'Menu' : 'Produits'}
          </label>
          <button type="button" onClick={handleProductAdd} style={{ padding: '5px 14px', background: `${NEON}20`, border: `1px solid ${NEON}40`, borderRadius: 6, color: NEON, fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>+ Ajouter</button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 280, overflowY: 'auto' }}>
          {config.products_services.map((item, index) => (
            <div key={index} style={{ padding: '10px', background: BG, borderRadius: 8, border: `1px solid ${BORDER}`, display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ display: 'flex', gap: 8 }}>
                <input type="text" placeholder="Nom" value={item.name} onChange={(e) => handleProductChange(index, 'name', e.target.value)} style={{ ...fieldStyle, flex: 1, padding: '6px 10px' }} />
                <input type="number" placeholder="Prix" value={item.price} onChange={(e) => handleProductChange(index, 'price', parseFloat(e.target.value))} style={{ ...fieldStyle, width: 80, padding: '6px 10px' }} />
                <input type="text" placeholder="Description" value={item.description} onChange={(e) => handleProductChange(index, 'description', e.target.value)} style={{ ...fieldStyle, flex: 2, padding: '6px 10px' }} />
                <button type="button" onClick={() => handleProductRemove(index)} style={{ padding: '6px 10px', background: '#FF444420', border: '1px solid #FF444440', borderRadius: 6, color: '#FF8888', fontSize: 12, cursor: 'pointer' }}>✕</button>
              </div>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                {item.image_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={item.image_url} alt={item.name} style={{ width: 48, height: 48, objectFit: 'cover', borderRadius: 6, border: `1px solid ${BORDER}`, flexShrink: 0 }} />
                )}
                <label style={{ ...fieldStyle, padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', width: 'auto', fontSize: 12, color: MUTED, boxSizing: 'border-box' as const }}>
                  📷 {item.image_url ? 'Changer la photo' : 'Ajouter une photo'}
                  <input
                    type="file"
                    accept="image/*"
                    style={{ display: 'none' }}
                    onChange={e => { if (e.target.files?.[0]) handleProductImage(index, e.target.files[0]); }}
                  />
                </label>
                {item.image_url && (
                  <button type="button" onClick={() => handleProductChange(index, 'image_url', '')} style={{ padding: '4px 10px', background: '#FF444420', border: '1px solid #FF444440', borderRadius: 6, color: '#FF8888', fontSize: 11, cursor: 'pointer', flexShrink: 0 }}>
                    Supprimer
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* E-commerce Specific */}
      {config.business_type_slug === 'ecommerce' && (
        <>
          <div>
            <label style={labelStyle}>Politique de retour</label>
            <textarea name="return_policy" value={config.return_policy} onChange={handleChange} placeholder="30 jours pour retourner les articles..." rows={2} style={{ ...fieldStyle, resize: 'vertical' as const }} />
          </div>
          <div>
            <label style={labelStyle}>Information de garantie</label>
            <textarea name="warranty_info" value={config.warranty_info} onChange={handleChange} placeholder="1 an de garantie sur tous les produits..." rows={2} style={{ ...fieldStyle, resize: 'vertical' as const }} />
          </div>
        </>
      )}

      {/* Submit */}
      <button type="submit" disabled={loading} style={{ width: '100%', padding: '12px', background: loading ? `${NEON}30` : NEON, border: 'none', borderRadius: 8, color: loading ? MUTED : '#06040E', fontSize: 13, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', transition: 'all 0.2s' }}>
        {loading ? 'Sauvegarde en cours...' : '💾 Sauvegarder la configuration'}
      </button>
    </form>
  );
}
