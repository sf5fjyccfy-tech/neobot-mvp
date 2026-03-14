'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiCall, setToken } from '@/lib/api';

interface SignupFormData {
  full_name: string;
  email: string;
  password: string;
  tenant_name: string;
  business_type: string;
}

const BUSINESS_TYPES = [
  { value: 'neobot', label: 'NéoBot (Notre plateforme)' },
  { value: 'restaurant', label: 'Restaurant' },
  { value: 'ecommerce', label: 'E-commerce' },
  { value: 'travel', label: 'Voyage & Tourisme' },
  { value: 'salon', label: 'Salon & Beauté' },
  { value: 'fitness', label: 'Fitness & Gym' },
  { value: 'consulting', label: 'Consulting' },
  { value: 'custom', label: 'Autre' },
];

export default function SignupForm() {
  const router = useRouter();
  const [formData, setFormData] = useState<SignupFormData>({
    full_name: '',
    email: '',
    password: '',
    tenant_name: '',
    business_type: 'restaurant',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await apiCall('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify(formData),
      });

      const data = await response.json();
      
      // Save token
      setToken(data.access_token);
      
      // Redirect to dashboard
      router.push('/dashboard');
    } catch (err) {
      setError('Erreur lors de l\'inscription. Vérifiez vos données.');
      console.error('Signup error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 w-full max-w-md mx-auto">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div>
        <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
          Nom complet
        </label>
        <input
          id="full_name"
          name="full_name"
          type="text"
          required
          value={formData.full_name}
          onChange={handleChange}
          className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Jean Dupont"
        />
      </div>

      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          value={formData.email}
          onChange={handleChange}
          className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="you@example.com"
        />
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          Mot de passe
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          value={formData.password}
          onChange={handleChange}
          className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="••••••••"
        />
      </div>

      <div>
        <label htmlFor="tenant_name" className="block text-sm font-medium text-gray-700">
          Nom de votre entreprise
        </label>
        <input
          id="tenant_name"
          name="tenant_name"
          type="text"
          required
          value={formData.tenant_name}
          onChange={handleChange}
          className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Ma Super Entreprise"
        />
      </div>

      <div>
        <label htmlFor="business_type" className="block text-sm font-medium text-gray-700">
          Type d'entreprise
        </label>
        <select
          id="business_type"
          name="business_type"
          value={formData.business_type}
          onChange={handleChange}
          className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {BUSINESS_TYPES.map(type => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-md transition"
      >
        {loading ? 'Inscription...' : 'S\'inscrire'}
      </button>

      <p className="text-center text-sm text-gray-600">
        Vous avez déjà un compte?{' '}
        <a href="/login" className="text-blue-600 hover:text-blue-700">
          Se connecter
        </a>
      </p>
    </form>
  );
}
