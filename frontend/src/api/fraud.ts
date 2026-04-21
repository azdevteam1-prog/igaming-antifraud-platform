import { apiClient } from './client';

export interface FraudAlert {
  id: string;
  player_id: string;
  player_username: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  risk_score: number;
  description: string;
  status: 'open' | 'investigating' | 'resolved' | 'dismissed';
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
}

export interface FraudStats {
  total_alerts: number;
  open_alerts: number;
  critical_alerts: number;
  resolved_today: number;
  avg_risk_score: number;
  alerts_by_type: Record<string, number>;
  alerts_by_severity: Record<string, number>;
}

export interface AlertsFilter {
  status?: string;
  severity?: string;
  alert_type?: string;
  player_id?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  limit?: number;
}

export const fraudApi = {
  getAlerts: async (filters?: AlertsFilter) => {
    const response = await apiClient.get('/fraud/alerts', { params: filters });
    return response.data;
  },

  getAlertById: async (alertId: string): Promise<FraudAlert> => {
    const response = await apiClient.get(`/fraud/alerts/${alertId}`);
    return response.data;
  },

  updateAlertStatus: async (
    alertId: string,
    status: FraudAlert['status'],
    notes?: string
  ): Promise<FraudAlert> => {
    const response = await apiClient.patch(`/fraud/alerts/${alertId}`, {
      status,
      notes,
    });
    return response.data;
  },

  getStats: async (): Promise<FraudStats> => {
    const response = await apiClient.get('/fraud/stats');
    return response.data;
  },

  getRiskScore: async (playerId: string) => {
    const response = await apiClient.get(`/fraud/risk-score/${playerId}`);
    return response.data;
  },

  runDetection: async (playerId: string) => {
    const response = await apiClient.post(`/fraud/detect/${playerId}`);
    return response.data;
  },
};
