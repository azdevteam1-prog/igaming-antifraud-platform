import { useEffect, useState } from 'react';
import { KpiCard } from '../components/KpiCard';
import { RiskBadge } from '../components/RiskBadge';
import { fraudApi, FraudStats } from '../api/fraud';
import { sessionsApi } from '../api/sessions';

export default function DashboardPage() {
  const [fraudStats, setFraudStats] = useState<FraudStats | null>(null);
  const [sessionStats, setSessionStats] = useState<{
    active_sessions: number;
    high_risk_sessions: number;
    countries: number;
  } | null>(null);
  const [recentAlerts, setRecentAlerts] = useState<
    Array<{
      id: string;
      player_username: string;
      alert_type: string;
      severity: string;
      risk_score: number;
      created_at: string;
    }>
  >([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [stats, sessions, alerts] = await Promise.all([
          fraudApi.getStats(),
          sessionsApi.getSessionStats(),
          fraudApi.getAlerts({ status: 'open', limit: 5 }),
        ]);
        setFraudStats(stats);
        setSessionStats(sessions);
        setRecentAlerts(alerts.items || alerts);
      } catch (err) {
        console.error('Dashboard load error:', err);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">iGaming Anti-Fraud Platform Overview</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Open Alerts"
          value={fraudStats?.open_alerts ?? 0}
          trend="up"
          color="red"
        />
        <KpiCard
          title="Critical Alerts"
          value={fraudStats?.critical_alerts ?? 0}
          trend="up"
          color="orange"
        />
        <KpiCard
          title="Active Sessions"
          value={sessionStats?.active_sessions ?? 0}
          trend="neutral"
          color="blue"
        />
        <KpiCard
          title="Avg Risk Score"
          value={`${(fraudStats?.avg_risk_score ?? 0).toFixed(1)}%`}
          trend="down"
          color="green"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Recent Open Alerts</h2>
          {recentAlerts.length === 0 ? (
            <p className="text-gray-400 text-sm">No open alerts</p>
          ) : (
            <div className="space-y-3">
              {recentAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-900 text-sm">
                      {alert.player_username}
                    </p>
                    <p className="text-xs text-gray-500">{alert.alert_type}</p>
                  </div>
                  <RiskBadge score={alert.risk_score} />
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Alerts by Type</h2>
          {fraudStats?.alerts_by_type ? (
            <div className="space-y-2">
              {Object.entries(fraudStats.alerts_by_type).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">
                    {type.replace(/_/g, ' ')}
                  </span>
                  <span className="font-semibold text-gray-900">{count as number}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No data available</p>
          )}
        </div>
      </div>
    </div>
  );
}
