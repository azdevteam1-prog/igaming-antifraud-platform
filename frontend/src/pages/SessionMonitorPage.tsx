import React, { useState, useEffect, useRef } from 'react';

interface Session {
  id: string;
  player_id: string;
  ip_address: string;
  country: string;
  device_type: string;
  browser: string;
  risk_score: number;
  is_flagged: boolean;
  started_at: string;
  last_activity: string;
  duration_minutes: number;
  actions_count: number;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const RiskBadge: React.FC<{ score: number }> = ({ score }) => {
  const level = score >= 75 ? 'critical' : score >= 50 ? 'high' : score >= 25 ? 'medium' : 'low';
  const styles = {
    critical: 'bg-red-900 text-red-300 border border-red-600',
    high: 'bg-orange-900 text-orange-300 border border-orange-600',
    medium: 'bg-yellow-900 text-yellow-300 border border-yellow-600',
    low: 'bg-green-900 text-green-300 border border-green-600',
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[level]}`}>
      {score.toFixed(0)} - {level.toUpperCase()}
    </span>
  );
};

const MOCK_SESSIONS: Session[] = [
  { id: '1', player_id: 'PLR-1234', ip_address: '185.220.101.12', country: 'RU', device_type: 'Desktop', browser: 'Chrome', risk_score: 82, is_flagged: true, started_at: new Date(Date.now() - 1200000).toISOString(), last_activity: new Date().toISOString(), duration_minutes: 20, actions_count: 145 },
  { id: '2', player_id: 'PLR-5678', ip_address: '92.38.172.44', country: 'UA', device_type: 'Mobile', browser: 'Safari', risk_score: 31, is_flagged: false, started_at: new Date(Date.now() - 600000).toISOString(), last_activity: new Date().toISOString(), duration_minutes: 10, actions_count: 43 },
  { id: '3', player_id: 'PLR-9012', ip_address: '10.0.0.1', country: 'DE', device_type: 'Desktop', browser: 'Firefox', risk_score: 15, is_flagged: false, started_at: new Date(Date.now() - 300000).toISOString(), last_activity: new Date().toISOString(), duration_minutes: 5, actions_count: 12 },
  { id: '4', player_id: 'PLR-3456', ip_address: '104.21.48.90', country: 'US', device_type: 'Tablet', browser: 'Chrome', risk_score: 55, is_flagged: true, started_at: new Date(Date.now() - 900000).toISOString(), last_activity: new Date().toISOString(), duration_minutes: 15, actions_count: 89 },
];

const SessionMonitorPage: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'flagged' | 'high_risk'>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchSessions = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API_BASE}/sessions/active`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('API unavailable');
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch {
      // Use mock data if API not available
      setSessions(MOCK_SESSIONS);
    } finally {
      setLoading(false);
      setLastUpdated(new Date());
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      timerRef.current = setInterval(fetchSessions, 15000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [autoRefresh]);

  const filtered = sessions.filter((s) => {
    if (filter === 'flagged') return s.is_flagged;
    if (filter === 'high_risk') return s.risk_score >= 50;
    return true;
  });

  const stats = {
    total: sessions.length,
    flagged: sessions.filter((s) => s.is_flagged).length,
    high_risk: sessions.filter((s) => s.risk_score >= 50).length,
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold">Session Monitor</h1>
            <p className="text-gray-400 text-sm mt-1">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          </div>
          <div className="flex gap-3 items-center">
            <label className="flex items-center gap-2 text-sm text-gray-400">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="accent-blue-500"
              />
              Auto-refresh (15s)
            </label>
            <button
              onClick={fetchSessions}
              className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-blue-400">{stats.total}</p>
            <p className="text-gray-400 text-sm">Active Sessions</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-red-400">{stats.flagged}</p>
            <p className="text-gray-400 text-sm">Flagged</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-orange-400">{stats.high_risk}</p>
            <p className="text-gray-400 text-sm">High Risk</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-2 mb-4">
          {(['all', 'flagged', 'high_risk'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                filter === f ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
              }`}
            >
              {f === 'all' ? 'All' : f === 'flagged' ? 'Flagged' : 'High Risk'}
            </button>
          ))}
        </div>

        {/* Session Table */}
        {loading ? (
          <div className="flex justify-center items-center h-48">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500" />
          </div>
        ) : (
          <div className="bg-gray-800 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-700">
                <tr>
                  {['Player ID', 'IP Address', 'Country', 'Device', 'Duration', 'Actions', 'Risk Score', 'Status'].map(
                    (h) => (
                      <th key={h} className="px-4 py-2 text-left text-gray-300 font-medium">
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filtered.map((session) => (
                  <tr
                    key={session.id}
                    className={`hover:bg-gray-750 transition-colors ${
                      session.is_flagged ? 'bg-red-950 bg-opacity-30' : ''
                    }`}
                  >
                    <td className="px-4 py-2 font-mono text-blue-400">{session.player_id}</td>
                    <td className="px-4 py-2 font-mono text-gray-300">{session.ip_address}</td>
                    <td className="px-4 py-2 text-gray-400">{session.country}</td>
                    <td className="px-4 py-2 text-gray-400">{session.device_type} / {session.browser}</td>
                    <td className="px-4 py-2 text-gray-300">{session.duration_minutes}m</td>
                    <td className="px-4 py-2 text-gray-300">{session.actions_count}</td>
                    <td className="px-4 py-2">
                      <RiskBadge score={session.risk_score} />
                    </td>
                    <td className="px-4 py-2">
                      {session.is_flagged ? (
                        <span className="text-red-400 text-xs font-medium">FLAGGED</span>
                      ) : (
                        <span className="text-green-500 text-xs">Active</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div className="text-center text-gray-500 py-8">No sessions match the current filter.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionMonitorPage;
