/** API client for the News Intelligence Platform backend. */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetcher<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(error.message || `API Error: ${res.status}`);
  }

  return res.json();
}

export const api = {
  // Health
  health: () => fetcher('/health'),

  // Events
  listEvents: () => fetcher<{ events: any[] }>('/api/v1/events').then(r => r.events),
  getEvent: (id: string) => fetcher<any>(`/api/v1/events/${id}`),

  // Reports
  listReports: () => fetcher<{ reports: any[] }>('/api/v1/reports').then(r => r.reports),
  getReport: (id: string) => fetcher<any>(`/api/v1/reports/${id}`),

  // Analysis
  analyze: (data: any) => fetcher<any>('/api/v1/events/analyze', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // Chat
  chat: (query: string) => fetcher<any>('/api/v1/chat/query', {
    method: 'POST',
    body: JSON.stringify({ query }),
  }),

  // Detect
  detect: (data: any) => fetcher<any>('/api/v1/events/detect', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
};
