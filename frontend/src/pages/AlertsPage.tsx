import { useState } from 'react';
import { useFraudAlerts } from '../hooks/useFraudAlerts';
import { RiskBadge } from '../components/RiskBadge';
import { StatusBadge } from '../components/StatusBadge';
import { FraudAlert } from '../api/fraud';

const SEVERITY_OPTIONS = ['all', 'low', 'medium', 'high', 'critical'];
const STATUS_OPTIONS = ['all', 'open', 'investigating', 'resolved', 'dismissed'];

export default function AlertsPage() {
  const [selectedAlert, setSelectedAlert] = useState<FraudAlert | null>(null);
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('open');

  const { alerts, isLoading, error, updateAlertStatus, refresh } =
    useFraudAlerts({
      severity: severityFilter === 'all' ? undefined : severityFilter,
      status: statusFilter === 'all' ? undefined : statusFilter,
    });

  const handleStatusChange = async (
    alertId: string,
    newStatus: FraudAlert['status']
  ) => {
    await updateAlertStatus(alertId, newStatus);
    setSelectedAlert(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Fraud Alerts</h1>
          <p className="text-gray-500 mt-1">Monitor and manage fraud alerts</p>
        </div>
        <button
          onClick={refresh}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      <div className="flex gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-600">Severity:</label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm"
          >
            {SEVERITY_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>
                {opt.charAt(0).toUpperCase() + opt.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-600">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>
                {opt.charAt(0).toUpperCase() + opt.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400">No alerts found</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Player</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Severity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {alerts.map((alert) => (
                <tr
                  key={alert.id}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => setSelectedAlert(alert)}
                >
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{alert.player_username}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{alert.alert_type.replace(/_/g, ' ')}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      alert.severity === 'critical' ? 'bg-red-100 text-red-800' :
                      alert.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                      alert.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {alert.severity}
                    </span>
                  </td>
                  <td className="px-6 py-4"><RiskBadge score={alert.risk_score} /></td>
                  <td className="px-6 py-4"><StatusBadge status={alert.status} /></td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(alert.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                      {alert.status === 'open' && (
                        <>
                          <button
                            onClick={() => handleStatusChange(alert.id, 'investigating')}
                            className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                          >
                            Investigate
                          </button>
                          <button
                            onClick={() => handleStatusChange(alert.id, 'dismissed')}
                            className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded hover:bg-gray-200"
                          >
                            Dismiss
                          </button>
                        </>
                      )}
                      {alert.status === 'investigating' && (
                        <button
                          onClick={() => handleStatusChange(alert.id, 'resolved')}
                          className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                        >
                          Resolve
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedAlert && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedAlert(null)}>
          <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">Alert Details</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Player:</span><span className="font-medium">{selectedAlert.player_username}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Type:</span><span>{selectedAlert.alert_type}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Severity:</span><span>{selectedAlert.severity}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Risk Score:</span><RiskBadge score={selectedAlert.risk_score} /></div>
              <div className="flex justify-between"><span className="text-gray-500">Status:</span><StatusBadge status={selectedAlert.status} /></div>
              <div><span className="text-gray-500">Description:</span><p className="mt-1">{selectedAlert.description}</p></div>
            </div>
            <button onClick={() => setSelectedAlert(null)} className="mt-6 w-full py-2 bg-gray-100 rounded-lg hover:bg-gray-200">
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
