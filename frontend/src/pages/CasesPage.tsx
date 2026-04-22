import { useState } from 'react';
import { StatusBadge } from '../components/StatusBadge';
import { RiskBadge } from '../components/RiskBadge';

type CaseStatus = 'open' | 'investigating' | 'resolved' | 'closed';
type CasePriority = 'low' | 'medium' | 'high' | 'critical';

interface FraudCase {
  id: string;
  title: string;
  player_username: string;
  status: CaseStatus;
  priority: CasePriority;
  risk_score: number;
  description: string;
  created_at: string;
  assigned_to?: string;
}

const MOCK_CASES: FraudCase[] = [
  {
    id: '1',
    title: 'Multi-accounting suspected',
    player_username: 'player_001',
    status: 'open',
    priority: 'high',
    risk_score: 87,
    description: 'Multiple accounts detected from same IP and device fingerprint.',
    created_at: new Date().toISOString(),
    assigned_to: 'analyst_1',
  },
  {
    id: '2',
    title: 'Unusual withdrawal pattern',
    player_username: 'player_042',
    status: 'investigating',
    priority: 'critical',
    risk_score: 95,
    description: 'Large withdrawal immediately after deposit with no gameplay.',
    created_at: new Date().toISOString(),
  },
  {
    id: '3',
    title: 'Bonus abuse detected',
    player_username: 'player_117',
    status: 'resolved',
    priority: 'medium',
    risk_score: 62,
    description: 'Player exploited welcome bonus through linked accounts.',
    created_at: new Date().toISOString(),
    assigned_to: 'analyst_2',
  },
];

const STATUS_OPTIONS: CaseStatus[] = ['open', 'investigating', 'resolved', 'closed'];
const PRIORITY_OPTIONS = ['all', 'low', 'medium', 'high', 'critical'];

const PRIORITY_COLORS: Record<CasePriority, string> = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
};

export default function CasesPage() {
  const [cases, setCases] = useState<FraudCase[]>(MOCK_CASES);
  const [selectedCase, setSelectedCase] = useState<FraudCase | null>(null);
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const filtered = cases.filter((c) => {
    const matchPriority = priorityFilter === 'all' || c.priority === priorityFilter;
    const matchStatus = statusFilter === 'all' || c.status === statusFilter;
    return matchPriority && matchStatus;
  });

  const handleStatusChange = (caseId: string, newStatus: CaseStatus) => {
    setCases((prev) =>
      prev.map((c) => (c.id === caseId ? { ...c, status: newStatus } : c))
    );
    setSelectedCase(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Fraud Cases</h1>
          <p className="text-gray-500 mt-1">Manage and investigate fraud cases</p>
        </div>
        <div className="text-sm text-gray-500">{filtered.length} cases</div>
      </div>

      <div className="flex gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-600">Priority:</label>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm"
          >
            {PRIORITY_OPTIONS.map((opt) => (
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
            {['all', ...STATUS_OPTIONS].map((opt) => (
              <option key={opt} value={opt}>
                {opt.charAt(0).toUpperCase() + opt.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {filtered.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400">No cases found</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Player</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {filtered.map((c) => (
                <tr
                  key={c.id}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => setSelectedCase(c)}
                >
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{c.title}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{c.player_username}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${PRIORITY_COLORS[c.priority]}`}>
                      {c.priority}
                    </span>
                  </td>
                  <td className="px-6 py-4"><RiskBadge score={c.risk_score} /></td>
                  <td className="px-6 py-4"><StatusBadge status={c.status} /></td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(c.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                      {c.status === 'open' && (
                        <button
                          onClick={() => handleStatusChange(c.id, 'investigating')}
                          className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                        >
                          Investigate
                        </button>
                      )}
                      {c.status === 'investigating' && (
                        <button
                          onClick={() => handleStatusChange(c.id, 'resolved')}
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

      {selectedCase && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedCase(null)}>
          <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">Case Details</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Title:</span><span className="font-medium">{selectedCase.title}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Player:</span><span>{selectedCase.player_username}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Priority:</span>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${PRIORITY_COLORS[selectedCase.priority]}`}>
                  {selectedCase.priority}
                </span>
              </div>
              <div className="flex justify-between"><span className="text-gray-500">Risk Score:</span><RiskBadge score={selectedCase.risk_score} /></div>
              <div className="flex justify-between"><span className="text-gray-500">Status:</span><StatusBadge status={selectedCase.status} /></div>
              {selectedCase.assigned_to && (
                <div className="flex justify-between"><span className="text-gray-500">Assigned to:</span><span>{selectedCase.assigned_to}</span></div>
              )}
              <div><span className="text-gray-500">Description:</span><p className="mt-1">{selectedCase.description}</p></div>
            </div>
            <button onClick={() => setSelectedCase(null)} className="mt-6 w-full py-2 bg-gray-100 rounded-lg hover:bg-gray-200">
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
