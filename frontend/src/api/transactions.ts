import { apiClient } from './client';

export type TransactionType = 'deposit' | 'withdrawal' | 'bet' | 'win' | 'bonus' | 'chargeback' | 'refund';
export type TransactionStatus = 'pending' | 'completed' | 'failed' | 'flagged' | 'blocked';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface Transaction {
  id: string;
  player_id: string;
  player_username: string;
  type: TransactionType;
  amount: number;
  currency: string;
  status: TransactionStatus;
  risk_level: RiskLevel;
  risk_score: number;
  payment_method: string;
  payment_provider: string;
  ip_address: string;
  country: string;
  device_fingerprint: string;
  created_at: string;
  processed_at: string | null;
  flags: string[];
  metadata: Record<string, unknown>;
}

export interface TransactionStats {
  total_volume: number;
  total_count: number;
  flagged_count: number;
  blocked_count: number;
  chargeback_count: number;
  chargeback_rate: number;
  avg_deposit: number;
  volume_by_currency: Record<string, number>;
  volume_by_type: Record<string, number>;
}

export interface TransactionsFilter {
  type?: TransactionType;
  status?: TransactionStatus;
  risk_level?: RiskLevel;
  player_id?: string;
  payment_method?: string;
  country?: string;
  amount_min?: number;
  amount_max?: number;
  from_date?: string;
  to_date?: string;
  page?: number;
  limit?: number;
}

export const transactionsApi = {
  getTransactions: async (filters?: TransactionsFilter) => {
    const response = await apiClient.get('/transactions', { params: filters });
    return response.data;
  },

  getTransactionById: async (txId: string): Promise<Transaction> => {
    const response = await apiClient.get(`/transactions/${txId}`);
    return response.data;
  },

  getStats: async (fromDate?: string, toDate?: string): Promise<TransactionStats> => {
    const response = await apiClient.get('/transactions/stats', {
      params: { from_date: fromDate, to_date: toDate },
    });
    return response.data;
  },

  flagTransaction: async (txId: string, reason: string): Promise<Transaction> => {
    const response = await apiClient.post(`/transactions/${txId}/flag`, { reason });
    return response.data;
  },

  blockTransaction: async (txId: string, reason: string): Promise<Transaction> => {
    const response = await apiClient.post(`/transactions/${txId}/block`, { reason });
    return response.data;
  },

  approveTransaction: async (txId: string): Promise<Transaction> => {
    const response = await apiClient.post(`/transactions/${txId}/approve`);
    return response.data;
  },

  getPlayerTransactions: async (playerId: string, filters?: TransactionsFilter) => {
    const response = await apiClient.get(`/transactions/player/${playerId}`, {
      params: filters,
    });
    return response.data;
  },
};
