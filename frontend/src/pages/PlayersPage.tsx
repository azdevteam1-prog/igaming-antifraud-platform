import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { RiskBadge } from '../components/RiskBadge';
import { fraudApi } from '../api/fraud';
import { AccountGraphView } from '../components/AccountGraphView';

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

type ProfileTab = 'overview' | 'graph';

export default function PlayersPage() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [riskDetails, setRiskDetails] = useState<unknown>(null);
  const [profileTab, setProfileTab] = useState<ProfileTab>('overview');

  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        const response = await apiClient.get<Player[]>('/players/');
        setPlayers(response.data);
      } catch (err) {
        console.error('Failed to fetch players:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchPlayers();
  }, []);

  const handleViewProfile = async (player: Player) => {
    setSelectedPlayer(player);
    setProfileTab('overview');
    setRiskDetails(null);
    try {
      const details = await fraudApi.getRiskScore(player.id);
      setRiskDetails(details);
    } catch (err) {
      console.error('Failed to fetch risk details:', err);
    }
  };

  const filteredPlayers = players.filter((p) => {
    const matchesSearch =
      p.username.toLowerCase().includes(search.toLowerCase()) ||
      p.email.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || p.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Players</h1>
        <p className="text-gray-500 text-sm mt-1">Manage and monitor player accounts</p>
      </div>

      {/* Filters */}
      <div className="flex gap-4 flex-wrap mb-4">
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

      {/* Table */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Loading players...</div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="px-4 py-3 text-left">Player</th>
                <th className="px-4 py-3 text-left">Country</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Risk Score</th>
                <th className="px-4 py-3 text-left">Deposits</th>
                <th className="px-4 py-3 text-left">Last Login</th>
                <th className="px-4 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {filteredPlayers.map((player) => (
                <tr key={player.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium text-gray-900">{player.username}</p>
                      <p className="text-xs text-gray-400">{player.email}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{player.country}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      player.status === 'active' ? 'bg-green-100 text-green-700' :
                      player.status === 'suspended' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {player.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <RiskBadge score={player.risk_score} />
                  </td>
                  <td className="px-4 py-3 text-gray-600">${player.total_deposits?.toLocaleString()}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {new Date(player.last_login).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleViewProfile(player)}
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                    >
                      View Profile
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredPlayers.length === 0 && (
            <div className="text-center py-8 text-gray-400">No players found.</div>
          )}
        </div>
      )}

      {/* Player Profile Modal */}
      {selectedPlayer && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
            {/* Modal header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{selectedPlayer.username}</h3>
                <p className="text-xs text-gray-400">{selectedPlayer.email}</p>
              </div>
              <button
                onClick={() => setSelectedPlayer(null)}
                className="text-gray-400 hover:text-gray-600 text-xl leading-none"
              >
                &times;
              </button>
            </div>

            {/* Tab bar */}
            <div className="flex border-b border-gray-100 px-6">
              <button
                onClick={() => setProfileTab('overview')}
                className={`py-3 px-4 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  profileTab === 'overview'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setProfileTab('graph')}
                className={`py-3 px-4 text-sm font-medium border-b-2 -mb-px transition-colors flex items-center gap-1.5 ${
                  profileTab === 'graph'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="5" cy="12" r="2" />
                  <circle cx="19" cy="5" r="2" />
                  <circle cx="19" cy="19" r="2" />
                  <line x1="7" y1="11.5" x2="17" y2="6" />
                  <line x1="7" y1="12.5" x2="17" y2="18" />
                </svg>
                Account Graph
              </button>
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-auto">
              {profileTab === 'overview' && (
                <div className="p-6 space-y-4 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Risk Score:</span>
                    <RiskBadge score={selectedPlayer.risk_score} />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Status:</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      selectedPlayer.status === 'active' ? 'bg-green-100 text-green-700' :
                      selectedPlayer.status === 'suspended' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {selectedPlayer.status}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Country:</span>
                    <span>{selectedPlayer.country}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Total Deposits:</span>
                    <span>${selectedPlayer.total_deposits?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Registered:</span>
                    <span>{new Date(selectedPlayer.registration_date).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Last Login:</span>
                    <span>{new Date(selectedPlayer.last_login).toLocaleDateString()}</span>
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
              )}

              {profileTab === 'graph' && (
                <div className="h-[480px]">
                  <AccountGraphView playerId={selectedPlayer.id} />
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
