// =============================================================================
// iGaming Anti-Fraud Platform — Shared TypeScript Type Definitions
// =============================================================================

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type TxType = 'deposit' | 'withdrawal' | 'bet' | 'win' | 'refund';

export type TxStatus = 'pending' | 'approved' | 'flagged' | 'blocked' | 'reversed';

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export type AlertStatus = 'open' | 'investigating' | 'resolved' | 'false_positive';

export type RuleCategory =
  | 'velocity'
  | 'amount'
  | 'geo'
  | 'device'
  | 'kyc'
  | 'bonus'
  | 'multi_account'
  | 'chargeback';

export type RuleConditionType =
  | 'threshold'
  | 'pattern'
  | 'blacklist'
  | 'whitelist'
  | 'ml_score';

export type RuleAction = 'review' | 'block' | 'flag' | 'notify';

export type RuleStatus = 'live' | 'shadow' | 'disabled';

// ---------------------------------------------------------------------------
// Player
// ---------------------------------------------------------------------------

export interface Player {
  id: string;
  username: string;
  email: string;
  country: string;
  currency: string;
  riskScore: number;          // 0-1
  kycVerified: boolean;
  pepFlag: boolean;
  sanctionsFlag: boolean;
  bonusAbuseFlag: boolean;
  multiAccountFlag: boolean;
  chargebacks: number;
  totalDeposits: number;
  totalWithdrawals: number;
  registeredAt: string;       // ISO 8601
  lastSeen: string | null;
  createdAt: string;
}

// ---------------------------------------------------------------------------
// Transaction
// ---------------------------------------------------------------------------

export interface Transaction {
  id: string;
  playerId: string;
  playerUsername?: string;
  txType: TxType;
  amount: number;
  currency: string;
  status: TxStatus;
  riskScore: number;          // 0-1
  ruleHits: RuleHit[];
  ipAddress: string | null;
  countryCode: string | null;
  deviceId: string | null;
  createdAt: string;
}

// ---------------------------------------------------------------------------
// Rule
// ---------------------------------------------------------------------------

export interface RuleConditionParams {
  field?: string;
  operator?: 'gt' | 'gte' | 'lt' | 'lte' | 'eq' | 'neq' | 'in' | 'nin' | 'regex';
  value?: number | string | string[];
  windowSeconds?: number;
  countField?: string;
}

export interface Rule {
  id: string;
  code: string;
  name: string;
  description: string;
  category: RuleCategory;
  conditionType: RuleConditionType;
  conditionParams: RuleConditionParams;
  riskPoints: number;         // 0-100
  action: RuleAction;
  status: RuleStatus;
  priority: number;
  createdAt: string;
  updatedAt: string;
}

export interface RuleHit {
  ruleCode: string;
  ruleName: string;
  riskPoints: number;
  action: RuleAction;
}

// ---------------------------------------------------------------------------
// Alert
// ---------------------------------------------------------------------------

export interface Alert {
  id: string;
  transactionId: string;
  playerId: string;
  playerUsername?: string;
  ruleCode: string;
  ruleName: string;
  riskScore: number;
  status: AlertStatus;
  assignedTo: string | null;
  notes: string | null;
  resolvedAt: string | null;
  createdAt: string;
}

// ---------------------------------------------------------------------------
// Device
// ---------------------------------------------------------------------------

export interface Device {
  id: string;
  playerId: string;
  fingerprint: string;
  browser: string | null;
  os: string | null;
  deviceType: 'mobile' | 'desktop' | 'tablet' | null;
  screenResolution: string | null;
  timezone: string | null;
  language: string | null;
  isTrusted: boolean;
  firstSeen: string;
  lastSeen: string;
}

// ---------------------------------------------------------------------------
// Dashboard & Analytics
// ---------------------------------------------------------------------------

export interface KpiSummary {
  totalPlayers: number;
  activePlayers24h: number;
  totalTransactions7d: number;
  flaggedTransactions7d: number;
  fraudRate7dPct: number;
  openAlerts: number;
  highRiskPlayers: number;
  generatedAt: string;
}

export interface FraudRateResponse {
  periodDays: number;
  totalTransactions: number;
  flaggedTransactions: number;
  fraudRatePct: number;
}

export interface AlertsByRule {
  ruleCode: string;
  alertCount: number;
}

export interface VolumeByType {
  txType: TxType;
  count: number;
  totalAmount: number;
  avgAmount: number;
}

export interface RiskDistributionBucket {
  bucket: RiskLevel;
  min: number;
  max: number;
  count: number;
}

// ---------------------------------------------------------------------------
// WebSocket
// ---------------------------------------------------------------------------

export interface WsTransactionEvent {
  type: 'transaction';
  data: Transaction;
}

export interface WsAlertEvent {
  type: 'alert';
  data: Alert;
}

export type WsEvent = WsTransactionEvent | WsAlertEvent;

// ---------------------------------------------------------------------------
// API Pagination
// ---------------------------------------------------------------------------

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
}

// ---------------------------------------------------------------------------
// Graph / Link Analysis
// ---------------------------------------------------------------------------

export interface GraphNode {
  id: string;
  label: string;
  type: 'player' | 'device' | 'ip' | 'email';
  riskScore?: number;
  flagged?: boolean;
}

export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
  label?: string;
}

export interface LinkGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ---------------------------------------------------------------------------
// Utility types
// ---------------------------------------------------------------------------

export type SortDirection = 'asc' | 'desc';

export interface SortParams {
  field: string;
  direction: SortDirection;
}

export interface FilterParams {
  [key: string]: string | number | boolean | null | undefined;
}
