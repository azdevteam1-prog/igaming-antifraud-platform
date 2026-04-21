import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { RiskBadge } from '../components/RiskBadge';
import { fraudApi } from '../api/fraud';

interface Player {
  id: string;
  username: string;
  email: string;
  country: string;
  status: 'active' | 'suspended' | 'banned';
  risk_score: number;
  total_deposits: number;
  registration_date: string;
  last_login: string;
  flags: string[];
}

export default function PlayersPage() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [riskDetails, setRiskDetails] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    const fetchPlayers = async () => {
      setIsLoading(true);
      try {
        const response = await apiClient.get('/players', {
          params: {
            search: search || undefined,
            status: statusFilter === 'all' ? undefined : statusFilter,
          },
        });
        setPlayers(response.data.items || response.data);
      } catch (err) {
        console.error('Failed to fetch players:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchPlayers();
  }, [search, statusFilter]);

  const handleViewRisk = async (player: Player) => {
    setSelectedPlayer(player);
    try {
      const details = await fraudApi.getRiskScore(player.id);
      setRiskDetails(details);
    } catch {
      setRiskDetails(null);
    }
  };

  const handleRunDetection = async (playerId: string) => {
    await fraudApi.runDetection(playerId);
    alert('Fraud detection initiated for player.');
  };

  const getStatusClass = (status: string) => {
    if (status === 'active') return 'bg-green-100 text-green-800';
    if (status === 'suspended') return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Players</h1>
        <p className="text-gray-500 mt-1">Search and manage player profiles</p>
      </div>

      <div className="flex gap-4 flex-wrap">
        <input
          type="text"
          placeholder="Search by username or email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-gray-200 rounded-lg px-4 py-2 text-sm flex-1 min-w-48"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
        >
          <option value="all">All Statuses</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="banned">Banned</option>
        </select>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : players.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400">No players found</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Player</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Country</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Login</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {players.map((player) => (
                <tr key={player.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{player.username}</p>
                      <p className="text-xs text-gray-500">{player.email}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{player.country}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusClass(player.status)}`}>
                      {player.status}
                    </span>
                  </td>
                  <td className="px-6 py-4"><RiskBadge score={player.risk_score} /></td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(player.last_login).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleViewRisk(player)}
                        className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                      >
                        Risk Profile
                      </button>
                      <button
                        onClick={() => handleRunDetection(player.id)}
                        className="text-xs px-2 py-1 bg-orange-100 text-orange-700 rounded hover:bg-orange-200"
                      >
                        Run Detection
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedPlayer && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedPlayer(null)}>
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">Risk Profile: {selectedPlayer.username}</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Risk Score:</span>
                <RiskBadge score={selectedPlayer.risk_score} />
              </div>
              {selectedPlayer.flags.length > 0 && (
                <div>
                  <p className="text-gray-500 mb-1">Flags:</p>
                  <div className="flex flex-wrap gap-1">
                    {selectedPlayer.flags.map((flag) => (
                      <span key={flag} className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs">
                        {flag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {riskDetails && (
                <div>
                  <p className="text-gray-500 mb-1">Risk Breakdown:</p>
                  <pre className="text-xs bg-gray-50 p-3 rounded overflow-auto max-h-32">
                    {JSON.stringify(riskDetails, null, 2)}
                  </pre>
                </div>
              )}
            </div>
            <button onClick={() => setSelectedPlayer(null)} className="mt-6 w-full py-2 bg-gray-100 rounded-lg hover:bg-gray-200">
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
