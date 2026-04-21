import { apiClient } from './client';

export interface PlayerSession {
  id: string;
  player_id: string;
  player_username: string;
  ip_address: string;
  country: string;
  device_type: string;
  browser: string;
  started_at: string;
  last_activity: string;
  status: 'active' | 'expired' | 'terminated';
  risk_score: number;
  flags: string[];
}

export interface SessionsFilter {
  status?: string;
  country?: string;
  player_id?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  limit?: number;
}

export const sessionsApi = {
  getSessions: async (filters?: SessionsFilter) => {
    const response = await apiClient.get('/sessions', { params: filters });
    return response.data;
  },

  getSessionById: async (sessionId: string): Promise<PlayerSession> => {
    const response = await apiClient.get(`/sessions/${sessionId}`);
    return response.data;
  },

  terminateSession: async (sessionId: string): Promise<void> => {
    await apiClient.post(`/sessions/${sessionId}/terminate`);
  },

  terminatePlayerSessions: async (playerId: string): Promise<void> => {
    await apiClient.post(`/sessions/player/${playerId}/terminate-all`);
  },

  getActiveSessions: async () => {
    const response = await apiClient.get('/sessions/active');
    return response.data;
  },

  getSessionStats: async () => {
    const response = await apiClient.get('/sessions/stats');
    return response.data;
  },
};
