import { useState, useEffect } from 'react';
import { rulesApi, FraudRule, RuleAction, RuleSeverity } from '../api/rules';

export default function RulesPage() {
  const [rules, setRules] = useState<FraudRule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newRuleName, setNewRuleName] = useState('');
  const [newRuleDesc, setNewRuleDesc] = useState('');
  const [newRuleSeverity, setNewRuleSeverity] = useState<RuleSeverity>('medium');
  const [newRuleAction, setNewRuleAction] = useState<RuleAction>('flag_alert');

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    setIsLoading(true);
    try {
      const data = await rulesApi.getRules();
      setRules(data);
    } catch (err) {
      console.error('Failed to load rules:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggle = async (ruleId: string, isActive: boolean) => {
    await rulesApi.toggleRule(ruleId, !isActive);
    await loadRules();
  };

  const handleDelete = async (ruleId: string) => {
    if (confirm('Delete this rule?')) {
      await rulesApi.deleteRule(ruleId);
      await loadRules();
    }
  };

  const handleCreate = async () => {
    if (!newRuleName.trim()) return;
    await rulesApi.createRule({
      name: newRuleName,
      description: newRuleDesc,
      severity: newRuleSeverity,
      action: newRuleAction,
      conditions: [
        { field: 'amount', operator: 'gt', value: 1000 },
      ],
    });
    setShowCreateModal(false);
    setNewRuleName('');
    setNewRuleDesc('');
    await loadRules();
  };

  const getSeverityColor = (severity: RuleSeverity) => {
    if (severity === 'critical') return 'bg-red-100 text-red-800';
    if (severity === 'high') return 'bg-orange-100 text-orange-800';
    if (severity === 'medium') return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Fraud Rules</h1>
          <p className="text-gray-500 mt-1">Create and manage fraud detection rules</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + Create Rule
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : rules.length === 0 ? (
        <div className="bg-white rounded-xl p-12 text-center">
          <p className="text-gray-400">No rules created yet. Click "Create Rule" to get started.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rules.map((rule) => (
            <div key={rule.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">{rule.name}</h3>
                    <span className={`px-2 py-0.5 text-xs rounded-full ${getSeverityColor(rule.severity)}`}>
                      {rule.severity}
                    </span>
                    {rule.is_active ? (
                      <span className="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700">Active</span>
                    ) : (
                      <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">Disabled</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{rule.description}</p>
                  <div className="flex gap-4 text-xs text-gray-500">
                    <span>Action: <span className="font-medium text-gray-700">{rule.action.replace(/_/g, ' ')}</span></span>
                    <span>Priority: <span className="font-medium text-gray-700">{rule.priority}</span></span>
                    <span>Triggers: <span className="font-medium text-gray-700">{rule.trigger_count}</span></span>
                    {rule.last_triggered && (
                      <span>Last: <span className="font-medium text-gray-700">{new Date(rule.last_triggered).toLocaleDateString()}</span></span>
                    )}
                  </div>
                  <div className="mt-3 p-3 bg-gray-50 rounded text-xs">
                    <span className="font-medium text-gray-600">Conditions:</span>
                    <div className="mt-1 space-y-1">
                      {rule.conditions.map((cond, idx) => (
                        <div key={cond.id} className="flex items-center gap-2">
                          {idx > 0 && <span className="text-gray-400">{cond.logical_operator || 'AND'}</span>}
                          <span className="font-medium">{cond.field}</span>
                          <span className="text-gray-500">{cond.operator}</span>
                          <span className="font-mono bg-white px-2 py-0.5 rounded">{String(cond.value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => handleToggle(rule.id, rule.is_active)}
                    className={`px-3 py-1 text-sm rounded ${
                      rule.is_active
                        ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                  >
                    {rule.is_active ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    onClick={() => handleDelete(rule.id)}
                    className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowCreateModal(false)}>
          <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">Create New Rule</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Rule Name</label>
                <input
                  type="text"
                  value={newRuleName}
                  onChange={(e) => setNewRuleName(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  placeholder="High deposit amount check"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Description</label>
                <textarea
                  value={newRuleDesc}
                  onChange={(e) => setNewRuleDesc(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Severity</label>
                  <select
                    value={newRuleSeverity}
                    onChange={(e) => setNewRuleSeverity(e.target.value as RuleSeverity)}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Action</label>
                  <select
                    value={newRuleAction}
                    onChange={(e) => setNewRuleAction(e.target.value as RuleAction)}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  >
                    <option value="flag_alert">Flag Alert</option>
                    <option value="block_transaction">Block Transaction</option>
                    <option value="suspend_player">Suspend Player</option>
                    <option value="require_kyc">Require KYC</option>
                    <option value="notify_analyst">Notify Analyst</option>
                  </select>
                </div>
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button
                onClick={handleCreate}
                className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create Rule
              </button>
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
