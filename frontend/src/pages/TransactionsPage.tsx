import { useState, useEffect } from 'react';
import { transactionsApi, Transaction, TransactionType, TransactionStatus, RiskLevel } from '../api/transactions';
import { RiskBadge } from '../components/RiskBadge';

const TYPE_OPTIONS: TransactionType[] = ['deposit', 'withdrawal', 'bet', 'win', 'bonus', 'chargeback', 'refund'];
const STATUS_OPTIONS: TransactionStatus[] = ['pending', 'completed', 'failed', 'flagged', 'blocked'];
const RISK_OPTIONS: RiskLevel[] = ['low', 'medium', 'high', 'critical'];

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [riskFilter, setRiskFilter] = useState<string>('all');
  const [searchPlayer, setSearchPlayer] = useState('');
  const [selectedTx, setSelectedTx] = useState<Transaction | null>(null);
  const [actionReason, setActionReason] = useState('');

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      try {
        const data = await transactionsApi.getTransactions({
          type: typeFilter === 'all' ? undefined : (typeFilter as TransactionType),
          status: statusFilter === 'all' ? undefined : (statusFilter as TransactionStatus),
          risk_level: riskFilter === 'all' ? undefined : (riskFilter as RiskLevel),
          player_id: searchPlayer || undefined,
        });
        setTransactions(data.items || data);
      } catch (err) {
        console.error('Failed to load transactions:', err);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [typeFilter, statusFilter, riskFilter, searchPlayer]);

  const handleFlag = async (txId: string) => {
    if (!actionReason.trim()) {
      alert('Please provide a reason');
      return;
    }
    await transactionsApi.flagTransaction(txId, actionReason);
    setActionReason('');
    setSelectedTx(null);
    window.location.reload();
  };

  const handleBlock = async (txId: string) => {
    if (!actionReason.trim()) {
      alert('Please provide a reason');
      return;
    }
    await transactionsApi.blockTransaction(txId, actionReason);
    setActionReason('');
    setSelectedTx(null);
    window.location.reload();
  };

  const handleApprove = async (txId: string) => {
    await transactionsApi.approveTransaction(txId);
    setSelectedTx(null);
    window.location.reload();
  };

  const getStatusBadge = (status: TransactionStatus) => {
    const colors: Record<TransactionStatus, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      flagged: 'bg-orange-100 text-orange-800',
      blocked: 'bg-gray-800 text-white',
    };
    return <span className={`px-2 py-0.5 text-xs rounded-full ${colors[status]}`}>{status}</span>;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
        <p className="text-gray-500 mt-1">Monitor and manage all player transactions</p>
      </div>

      <div className="flex gap-3 flex-wrap">
        <input
          type="text"
          placeholder="Search by player ID/username..."
          value={searchPlayer}
          onChange={(e) => setSearchPlayer(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm flex-1 min-w-48"
        />
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="border border-gray-200 rounded-lg px-3 py-2 text-sm">
          <option value="all">All Types</option>
          {TYPE_OPTIONS.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="border border-gray-200 rounded-lg px-3 py-2 text-sm">
          <option value="all">All Statuses</option>
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)} className="border border-gray-200 rounded-lg px-3 py-2 text-sm">
          <option value="all">All Risk Levels</option>
          {RISK_OPTIONS.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : transactions.length === 0 ? (
          <div className="text-center py-12"><p className="text-gray-400">No transactions found</p></div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Player</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Country</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {transactions.map((tx) => (
                <tr key={tx.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedTx(tx)}>
                  <td className="px-6 py-4 text-xs text-gray-500">{tx.id.slice(0, 8)}</td>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{tx.player_username}</td>
                  <td className="px-6 py-4 text-sm capitalize">{tx.type}</td>
                  <td className="px-6 py-4 text-sm font-semibold">{tx.amount.toFixed(2)} {tx.currency}</td>
                  <td className="px-6 py-4">{getStatusBadge(tx.status)}</td>
                  <td className="px-6 py-4"><RiskBadge score={tx.risk_score} /></td>
                  <td className="px-6 py-4 text-sm text-gray-600">{tx.country}</td>
                  <td className="px-6 py-4">
                    <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                      {tx.status === 'pending' && (
                        <>
                          <button onClick={() => handleApprove(tx.id)} className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200">Approve</button>
                          <button onClick={() => { setSelectedTx(tx); setActionReason(''); }} className="text-xs px-2 py-1 bg-orange-100 text-orange-700 rounded hover:bg-orange-200">Flag</button>
                          <button onClick={() => { setSelectedTx(tx); setActionReason(''); }} className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200">Block</button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedTx && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedTx(null)}>
          <div className="bg-white rounded-xl p-6 max-w-2xl w-full mx-4 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">Transaction Details</h3>
            <div className="grid grid-cols-2 gap-4 text-sm mb-6">
              <div><span className="text-gray-500">ID:</span> <span className="font-mono">{selectedTx.id}</span></div>
              <div><span className="text-gray-500">Player:</span> <span>{selectedTx.player_username}</span></div>
              <div><span className="text-gray-500">Type:</span> <span className="capitalize">{selectedTx.type}</span></div>
              <div><span className="text-gray-500">Amount:</span> <span className="font-semibold">{selectedTx.amount} {selectedTx.currency}</span></div>
              <div><span className="text-gray-500">Status:</span> {getStatusBadge(selectedTx.status)}</div>
              <div><span className="text-gray-500">Risk Score:</span> <RiskBadge score={selectedTx.risk_score} /></div>
              <div><span className="text-gray-500">Payment Method:</span> <span>{selectedTx.payment_method}</span></div>
              <div><span className="text-gray-500">Country:</span> <span>{selectedTx.country}</span></div>
              <div><span className="text-gray-500">IP:</span> <span className="font-mono text-xs">{selectedTx.ip_address}</span></div>
              <div><span className="text-gray-500">Created:</span> <span>{new Date(selectedTx.created_at).toLocaleString()}</span></div>
              {selectedTx.flags.length > 0 && (
                <div className="col-span-2">
                  <span className="text-gray-500">Flags:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedTx.flags.map((f) => <span key={f} className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs">{f}</span>)}
                  </div>
                </div>
              )}
            </div>
            {selectedTx.status === 'pending' && (
              <div className="space-y-3 border-t pt-4">
                <input
                  type="text"
                  placeholder="Reason for action..."
                  value={actionReason}
                  onChange={(e) => setActionReason(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                />
                <div className="flex gap-2">
                  <button onClick={() => handleFlag(selectedTx.id)} className="px-4 py-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200">Flag Transaction</button>
                  <button onClick={() => handleBlock(selectedTx.id)} className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200">Block Transaction</button>
                </div>
              </div>
            )}
            <button onClick={() => setSelectedTx(null)} className="mt-4 w-full py-2 bg-gray-100 rounded-lg hover:bg-gray-200">Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
