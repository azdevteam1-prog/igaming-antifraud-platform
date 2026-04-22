import { apiClient } from './client';

export type RuleConditionField =
  | 'amount'
  | 'transaction_type'
  | 'country'
  | 'payment_method'
  | 'ip_address'
  | 'risk_score'
  | 'deposit_count_24h'
  | 'withdrawal_count_24h'
  | 'total_deposits_7d'
  | 'session_duration'
  | 'device_fingerprint'
  | 'player_age_days';

export type RuleOperator =
  | 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte'
  | 'in' | 'not_in' | 'contains' | 'starts_with';

export type RuleAction =
  | 'flag_alert'
  | 'block_transaction'
  | 'suspend_player'
  | 'require_kyc'
  | 'notify_analyst'
  | 'increase_risk_score'
  | 'trigger_manual_review';

export type RuleSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface RuleCondition {
  id: string;
  field: RuleConditionField;
  operator: RuleOperator;
  value: string | number | string[];
  logical_operator?: 'AND' | 'OR';
}

export interface FraudRule {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  severity: RuleSeverity;
  conditions: RuleCondition[];
  action: RuleAction;
  action_params: Record<string, unknown>;
  priority: number;
  trigger_count: number;
  last_triggered: string | null;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface CreateRulePayload {
  name: string;
  description: string;
  severity: RuleSeverity;
  conditions: Omit<RuleCondition, 'id'>[];
  action: RuleAction;
  action_params?: Record<string, unknown>;
  priority?: number;
}

export const rulesApi = {
  getRules: async () => {
    const response = await apiClient.get('/rules');
    return response.data as FraudRule[];
  },

  getRuleById: async (ruleId: string): Promise<FraudRule> => {
    const response = await apiClient.get(`/rules/${ruleId}`);
    return response.data;
  },

  createRule: async (payload: CreateRulePayload): Promise<FraudRule> => {
    const response = await apiClient.post('/rules', payload);
    return response.data;
  },

  updateRule: async (
    ruleId: string,
    payload: Partial<CreateRulePayload>
  ): Promise<FraudRule> => {
    const response = await apiClient.put(`/rules/${ruleId}`, payload);
    return response.data;
  },

  toggleRule: async (ruleId: string, isActive: boolean): Promise<FraudRule> => {
    const response = await apiClient.patch(`/rules/${ruleId}/toggle`, {
      is_active: isActive,
    });
    return response.data;
  },

  deleteRule: async (ruleId: string): Promise<void> => {
    await apiClient.delete(`/rules/${ruleId}`);
  },

  testRule: async (
    ruleId: string,
    sampleData: Record<string, unknown>
  ) => {
    const response = await apiClient.post(`/rules/${ruleId}/test`, sampleData);
    return response.data;
  },

  getRuleStats: async () => {
    const response = await apiClient.get('/rules/stats');
    return response.data;
  },
};
