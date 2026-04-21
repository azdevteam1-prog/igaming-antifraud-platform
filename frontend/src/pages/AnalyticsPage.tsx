import React, { useState, useEffect } from 'react';

interface AnalyticsSummary {
  total_transactions: number;
  flagged_transactions: number;
  fraud_rate: number;
  total_alerts: number;
  open_alerts: number;
  avg_risk_score: number;
  top_fraud_types: { type: string; count: number }[];
  risk_distribution: { level: string; count: number }[];
  daily_stats: { date: string; transactions: number; flagged: number }[];
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const MetricCard: React.FC<{
  title: string;
  value: string | number;
  subtitle?: string;
  color?: string;
}> = ({ title, value, subtitle, color = 'blue' }) => {
  const colorMap: Record<string, string> = {
    blue: 'border-blue-500 text-blue-400',
    red: 'border-red-500 text-red-400',
    yellow: 'border-yellow-500 text-yellow-400',
    green: 'border-green-500 text-green-400',
  };
  return (
    <div className={`bg-gray-800 rounded-lg p-4 border-l-4 ${colorMap[color] || colorMap.blue}`}>
      <p className="text-gray-400 text-sm">{title}</p>
      <p className={`text-2xl font-bold mt-1 ${colorMap[color]?.split(' ')[1]}`}>{value}</p>
      {subtitle && <p className="text-gray-500 text-xs mt-1">{subtitle}</p>}
    </div>
  );
};

const BarChart: React.FC<{ data: { label: string; value: number }[]; title: string }> = ({ data, title }) => {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-gray-300 font-semibold mb-3">{title}</h3>
      <div className="space-y-2">
        {data.map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <span className="text-gray-400 text-xs w-32 truncate">{item.label}</span>
            <div className="flex-1 bg-gray-700 rounded-full h-4">
              <div
                className="bg-blue-500 h-4 rounded-full transition-all duration-500"
                style={{ width: `${(item.value / max) * 100}%` }}
              />
            </div>
            <span className="text-gray-300 text-xs w-8 text-right">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const AnalyticsPage: React.FC = () => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(`${API_BASE}/analytics/summary?period=${period}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setSummary(data);
      } catch (err) {
        setError('Failed to load analytics data.');
        // Fallback mock data for development
        setSummary({
          total_transactions: 15420,
          flagged_transactions: 312,
          fraud_rate: 2.02,
          total_alerts: 87,
          open_alerts: 23,
          avg_risk_score: 34.5,
          top_fraud_types: [
            { type: 'Multi-Accounting', count: 89 },
            { type: 'Bonus Abuse', count: 67 },
            { type: 'Payment Fraud', count: 54 },
            { type: 'Account Takeover', count: 32 },
            { type: 'Money Laundering', count: 18 },
          ],
          risk_distribution: [
            { level: 'Low', count: 11200 },
            { level: 'Medium', count: 3100 },
            { level: 'High', count: 890 },
            { level: 'Critical', count: 230 },
          ],
          daily_stats: [],
        });
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [period]);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Analytics Dashboard</h1>
            <p className="text-gray-400 text-sm mt-1">Fraud detection metrics and insights</p>
          </div>
          <div className="flex gap-2">
            {(['7d', '30d', '90d'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  period === p
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {loading && (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
          </div>
        )}

        {!loading && summary && (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
              <MetricCard title="Total Transactions" value={summary.total_transactions.toLocaleString()} color="blue" />
              <MetricCard title="Flagged" value={summary.flagged_transactions.toLocaleString()} color="yellow" />
              <MetricCard title="Fraud Rate" value={`${summary.fraud_rate.toFixed(2)}%`} color="red" />
              <MetricCard title="Total Alerts" value={summary.total_alerts} color="yellow" />
              <MetricCard title="Open Alerts" value={summary.open_alerts} color="red" />
              <MetricCard title="Avg Risk Score" value={summary.avg_risk_score.toFixed(1)} subtitle="/100" color="green" />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <BarChart
                title="Top Fraud Types"
                data={summary.top_fraud_types.map((f) => ({ label: f.type, value: f.count }))}
              />
              <BarChart
                title="Risk Distribution"
                data={summary.risk_distribution.map((r) => ({ label: r.level, value: r.count }))}
              />
            </div>

            {/* Alert Banner */}
            {error && (
              <div className="bg-yellow-900 border border-yellow-600 text-yellow-200 px-4 py-2 rounded text-sm">
                Note: Showing demo data. {error}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AnalyticsPage;
