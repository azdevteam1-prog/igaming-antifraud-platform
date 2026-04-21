import { useState } from 'react';
import { apiClient } from '../api/client';

const REPORT_TYPES = [
  { id: 'fraud_summary', label: 'Fraud Summary Report', description: 'Overview of all fraud alerts and resolutions' },
  { id: 'risk_distribution', label: 'Risk Score Distribution', description: 'Player risk score breakdown by category' },
  { id: 'alert_trends', label: 'Alert Trends', description: 'Daily/weekly/monthly alert volume trends' },
  { id: 'session_anomalies', label: 'Session Anomalies', description: 'Suspicious session patterns and geo anomalies' },
  { id: 'player_activity', label: 'Player Activity Report', description: 'Detailed player transaction and activity report' },
  { id: 'aml_compliance', label: 'AML Compliance Report', description: 'Anti-money laundering compliance summary' },
];

export default function ReportsPage() {
  const [selectedReport, setSelectedReport] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [format, setFormat] = useState('pdf');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleGenerateReport = async () => {
    if (!selectedReport) {
      setError('Please select a report type');
      return;
    }
    setIsGenerating(true);
    setError(null);
    setSuccess(null);
    try {
      const response = await apiClient.post(
        '/reports/generate',
        {
          report_type: selectedReport,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
          format,
        },
        { responseType: format === 'json' ? 'json' : 'blob' }
      );
      if (format === 'json') {
        const blob = new Blob([JSON.stringify(response.data, null, 2)], {
          type: 'application/json',
        });
        downloadBlob(blob, `${selectedReport}_report.json`);
      } else {
        downloadBlob(response.data as Blob, `${selectedReport}_report.${format}`);
      }
      setSuccess(`Report generated successfully!`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to generate report');
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <p className="text-gray-500 mt-1">Generate compliance and fraud analysis reports</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Select Report Type</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {REPORT_TYPES.map((report) => (
                <button
                  key={report.id}
                  onClick={() => setSelectedReport(report.id)}
                  className={`text-left p-4 rounded-lg border-2 transition-all ${
                    selectedReport === report.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-100 hover:border-gray-200 bg-gray-50'
                  }`}
                >
                  <p className={`font-medium text-sm ${
                    selectedReport === report.id ? 'text-blue-700' : 'text-gray-900'
                  }`}>
                    {report.label}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">{report.description}</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Report Options</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Date From</label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Date To</label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Format</label>
                <select
                  value={format}
                  onChange={(e) => setFormat(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="pdf">PDF</option>
                  <option value="csv">CSV</option>
                  <option value="xlsx">Excel (XLSX)</option>
                  <option value="json">JSON</option>
                </select>
              </div>
            </div>

            {error && (
              <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
                {error}
              </div>
            )}
            {success && (
              <div className="mt-4 bg-green-50 border border-green-200 text-green-700 px-3 py-2 rounded-lg text-sm">
                {success}
              </div>
            )}

            <button
              onClick={handleGenerateReport}
              disabled={isGenerating || !selectedReport}
              className="mt-6 w-full py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {isGenerating ? 'Generating...' : 'Generate Report'}
            </button>
          </div>

          {selectedReport && (
            <div className="bg-blue-50 rounded-xl border border-blue-100 p-4">
              <p className="text-sm font-medium text-blue-800">
                {REPORT_TYPES.find((r) => r.id === selectedReport)?.label}
              </p>
              <p className="text-xs text-blue-600 mt-1">
                {REPORT_TYPES.find((r) => r.id === selectedReport)?.description}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
