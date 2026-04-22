import { useEffect, useState, useCallback } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import { apiClient } from '../api/client';

// ─── Types ────────────────────────────────────────────────────────────────────

interface GraphNode {
  data: {
    id: string;
    label: string;
    risk_score: number;
    status: string;
    is_root: boolean;
    risk_label: string;
  };
}

interface GraphEdge {
  data: {
    id: string;
    source: string;
    target: string;
    relation: 'shared_device' | 'shared_ip';
  };
}

interface GraphData {
  player_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
}

interface Props {
  playerId: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function riskColor(score: number): string {
  if (score >= 80) return '#ef4444'; // red-500
  if (score >= 60) return '#f97316'; // orange-500
  if (score >= 40) return '#eab308'; // yellow-500
  return '#22c55e';                  // green-500
}

function edgeColor(relation: string): string {
  return relation === 'shared_device' ? '#8b5cf6' : '#3b82f6';
}

// ─── Cytoscape stylesheet ─────────────────────────────────────────────────────

const STYLESHEET: cytoscape.Stylesheet[] = [
  {
    selector: 'node',
    style: {
      label: 'data(label)',
      'font-size': '11px',
      'text-valign': 'bottom',
      'text-margin-y': 4,
      'text-wrap': 'wrap',
      'text-max-width': '80px',
      width: 36,
      height: 36,
      'background-color': '#6b7280',
      'border-width': 2,
      'border-color': '#374151',
      color: '#f9fafb',
    } as cytoscape.NodeSingularTraversing,
  },
  {
    selector: 'node[is_root = 1]',
    style: {
      width: 48,
      height: 48,
      'border-width': 3,
      'border-color': '#facc15',
      'font-size': '12px',
      'font-weight': 'bold',
    } as cytoscape.NodeSingularTraversing,
  },
  {
    selector: 'edge',
    style: {
      width: 2,
      'line-color': '#4b5563',
      'target-arrow-color': '#4b5563',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      label: 'data(relation)',
      'font-size': '9px',
      color: '#9ca3af',
      'text-rotation': 'autorotate',
    } as cytoscape.EdgeSingularTraversing,
  },
];

// ─── Component ────────────────────────────────────────────────────────────────

export function AccountGraphView({ playerId }: Props) {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [depth, setDepth] = useState(2);
  const [selectedElement, setSelectedElement] = useState<{
    type: 'node' | 'edge';
    data: Record<string, unknown>;
  } | null>(null);

  const fetchGraph = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<GraphData>(
        `/players/${playerId}/graph?depth=${depth}`
      );
      setGraphData(response.data);
    } catch (err) {
      setError('Failed to load account graph. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [playerId, depth]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  // Build elements with dynamic node colours derived from risk_score
  const elements = graphData
    ? [
        ...graphData.nodes.map((n) => ({
          ...n,
          data: {
            ...n.data,
            // Cytoscape needs numeric 1/0 for the is_root selector
            is_root: n.data.is_root ? 1 : 0,
            // Attach colour directly so it can be read in the style fn below
            nodeColor: riskColor(n.data.risk_score),
          },
        })),
        ...graphData.edges.map((e) => ({
          ...e,
          data: {
            ...e.data,
            edgeColor: edgeColor(e.data.relation),
          },
        })),
      ]
    : [];

  // Merge dynamic colours into stylesheet per-element is not natively
  // supported; use a mapper stylesheet that reads data() fields.
  const dynamicStylesheet: cytoscape.Stylesheet[] = [
    ...STYLESHEET,
    {
      selector: 'node',
      style: { 'background-color': 'data(nodeColor)' } as cytoscape.NodeSingularTraversing,
    },
    {
      selector: 'edge',
      style: {
        'line-color': 'data(edgeColor)',
        'target-arrow-color': 'data(edgeColor)',
      } as cytoscape.EdgeSingularTraversing,
    },
  ];

  return (
    <div className="flex flex-col h-full">
      {/* ── Toolbar ── */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700 bg-gray-800 rounded-t-lg gap-4">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-gray-300 uppercase tracking-wide">
            Account Network Graph
          </span>
          {graphData && (
            <span className="text-xs text-gray-400">
              {graphData.total_nodes} nodes &middot; {graphData.total_edges} edges
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-400">Depth:</label>
          <select
            value={depth}
            onChange={(e) => setDepth(Number(e.target.value))}
            className="text-xs bg-gray-700 text-gray-200 border border-gray-600 rounded px-2 py-0.5"
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
          </select>
          <button
            onClick={fetchGraph}
            className="text-xs bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* ── Legend ── */}
      <div className="flex items-center gap-4 px-4 py-1.5 bg-gray-800 border-b border-gray-700 text-xs text-gray-400">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-full bg-green-500" /> Low risk
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-full bg-yellow-400" /> Medium
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-full bg-orange-500" /> High
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-full bg-red-500" /> Critical
        </span>
        <span className="flex items-center gap-1 ml-4">
          <span className="inline-block w-5 border-t-2 border-purple-400" /> Shared device
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-5 border-t-2 border-blue-400" /> Shared IP
        </span>
        <span className="flex items-center gap-1 ml-2">
          <span className="inline-block w-3 h-3 rounded-full border-2 border-yellow-400 bg-transparent" /> Root player
        </span>
      </div>

      {/* ── Main canvas area ── */}
      <div className="flex flex-1 min-h-0">
        <div className="flex-1 relative bg-gray-900 rounded-b-lg">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center z-10">
              <div className="flex flex-col items-center gap-3">
                <div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-gray-400">Building graph...</span>
              </div>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 flex items-center justify-center z-10">
              <div className="text-center">
                <p className="text-red-400 text-sm mb-3">{error}</p>
                <button
                  onClick={fetchGraph}
                  className="text-xs bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded"
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          {!isLoading && !error && elements.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center">
              <p className="text-gray-500 text-sm">No linked accounts found.</p>
            </div>
          )}

          {!isLoading && !error && elements.length > 0 && (
            <CytoscapeComponent
              elements={elements}
              stylesheet={dynamicStylesheet}
              layout={{ name: 'cose', animate: true, randomize: false, nodeRepulsion: () => 8000 } as cytoscape.LayoutOptions}
              style={{ width: '100%', height: '100%' }}
              cy={(cy) => {
                cy.on('tap', 'node', (evt) => {
                  setSelectedElement({ type: 'node', data: evt.target.data() as Record<string, unknown> });
                });
                cy.on('tap', 'edge', (evt) => {
                  setSelectedElement({ type: 'edge', data: evt.target.data() as Record<string, unknown> });
                });
                cy.on('tap', (evt) => {
                  if (evt.target === cy) setSelectedElement(null);
                });
              }}
            />
          )}
        </div>

        {/* ── Inspector panel ── */}
        {selectedElement && (
          <div className="w-56 flex-shrink-0 bg-gray-800 border-l border-gray-700 p-3 overflow-y-auto text-xs text-gray-300 space-y-2">
            <p className="font-semibold text-gray-100 uppercase tracking-wide text-xs">
              {selectedElement.type === 'node' ? 'Account' : 'Connection'}
            </p>
            {Object.entries(selectedElement.data)
              .filter(([k]) => !['nodeColor', 'edgeColor'].includes(k))
              .map(([k, v]) => (
                <div key={k} className="flex justify-between gap-2">
                  <span className="text-gray-400 truncate">{k}</span>
                  <span className="text-gray-100 truncate">{String(v)}</span>
                </div>
              ))}
            <button
              onClick={() => setSelectedElement(null)}
              className="mt-2 w-full py-1 bg-gray-700 hover:bg-gray-600 rounded text-gray-300"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
