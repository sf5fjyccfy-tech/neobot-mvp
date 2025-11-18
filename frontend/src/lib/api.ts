const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = {
  async get(endpoint: string) {
    const res = await fetch(`${API_URL}${endpoint}`)
    if (!res.ok) throw new Error(`API Error: ${res.status}`)
    return res.json()
  },

  async post(endpoint: string, data: any) {
    const res = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error(`API Error: ${res.status}`)
    return res.json()
  },

  async put(endpoint: string, data: any) {
    const res = await fetch(`${API_URL}${endpoint}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error(`API Error: ${res.status}`)
    return res.json()
  },

  async delete(endpoint: string) {
    const res = await fetch(`${API_URL}${endpoint}`, {
      method: 'DELETE'
    })
    if (!res.ok) throw new Error(`API Error: ${res.status}`)
    return res.json()
  },

  // SEULEMENT LES MÉTHODES QUI EXISTENT RÉELLEMENT
  async getAnalytics(tenantId: string, period?: string) {
    const url = period
      ? `/api/tenants/${tenantId}/analytics?period=${period}`
      : `/api/tenants/${tenantId}/analytics`
    return this.get(url)
  }
}
