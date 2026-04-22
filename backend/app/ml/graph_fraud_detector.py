import networkx as nx
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Set, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class GraphFraudDetector:
    """NetworkX-based graph analytics for multi-accounting detection.
    
    Use cases:
    - Detect account rings (groups of connected fraudulent accounts)
    - Find community structures in player networks
    - Calculate centrality scores for suspicious accounts
    - Identify bridging accounts connecting multiple fraud rings
    - Analyze transaction flow patterns
    """
    
    def __init__(self):
        self.player_graph = nx.Graph()
        self.device_graph = nx.Graph()
        self.ip_graph = nx.Graph()
        self.transaction_graph = nx.DiGraph()  # Directed for money flow
    
    # ===== Graph Building =====
    
    def add_player_connection(self, player1_id: str, player2_id: str, 
                             connection_type: str, weight: float = 1.0,
                             metadata: Optional[Dict] = None):
        """Add edge between players based on shared attributes.
        
        Connection types:
        - 'shared_device': Same device fingerprint
        - 'shared_ip': Same IP address
        - 'shared_email': Similar email pattern
        - 'shared_payment': Same payment method
        - 'referral': One referred the other
        """
        if not self.player_graph.has_edge(player1_id, player2_id):
            self.player_graph.add_edge(
                player1_id, player2_id,
                connection_type=connection_type,
                weight=weight,
                created_at=datetime.utcnow(),
                metadata=metadata or {}
            )
        else:
            # Strengthen existing connection
            current_weight = self.player_graph[player1_id][player2_id].get('weight', 1.0)
            self.player_graph[player1_id][player2_id]['weight'] = current_weight + weight
    
    def build_device_network(self, device_player_map: Dict[str, List[str]]):
        """Build bipartite graph of devices and players."""
        for device_id, player_ids in device_player_map.items():
            for player_id in player_ids:
                self.device_graph.add_node(device_id, node_type='device')
                self.device_graph.add_node(player_id, node_type='player')
                self.device_graph.add_edge(device_id, player_id, 
                                          created_at=datetime.utcnow())
            
            # Connect players who share this device
            for i, p1 in enumerate(player_ids):
                for p2 in player_ids[i+1:]:
                    self.add_player_connection(p1, p2, 'shared_device', weight=2.0,
                                              metadata={'device_id': device_id})
    
    def build_ip_network(self, ip_player_map: Dict[str, List[str]]):
        """Build bipartite graph of IPs and players."""
        for ip_address, player_ids in ip_player_map.items():
            # Only connect if 2-5 players share IP (avoid WiFi/household false positives)
            if 2 <= len(player_ids) <= 5:
                for i, p1 in enumerate(player_ids):
                    for p2 in player_ids[i+1:]:
                        self.add_player_connection(p1, p2, 'shared_ip', weight=1.5,
                                                  metadata={'ip_address': ip_address})
    
    def add_transaction_edge(self, from_player: str, to_player: str, 
                            amount: float, timestamp: datetime):
        """Add directed edge for money flow between players."""
        if not self.transaction_graph.has_edge(from_player, to_player):
            self.transaction_graph.add_edge(
                from_player, to_player,
                total_amount=amount,
                transaction_count=1,
                first_tx=timestamp,
                last_tx=timestamp
            )
        else:
            edge_data = self.transaction_graph[from_player][to_player]
            edge_data['total_amount'] += amount
            edge_data['transaction_count'] += 1
            edge_data['last_tx'] = timestamp
    
    # ===== Fraud Ring Detection =====
    
    def detect_fraud_rings(self, min_ring_size: int = 3) -> List[Set[str]]:
        """Detect connected components (potential fraud rings)."""
        rings = []
        
        # Find connected components
        components = list(nx.connected_components(self.player_graph))
        
        for component in components:
            if len(component) >= min_ring_size:
                # Calculate ring metrics
                subgraph = self.player_graph.subgraph(component)
                density = nx.density(subgraph)
                
                # High density = tightly connected = suspicious
                if density > 0.3:  # Threshold tunable
                    rings.append({
                        'players': list(component),
                        'size': len(component),
                        'density': density,
                        'risk_score': self._calculate_ring_risk(subgraph)
                    })
        
        # Sort by risk score
        return sorted(rings, key=lambda x: x['risk_score'], reverse=True)
    
    def _calculate_ring_risk(self, subgraph: nx.Graph) -> float:
        """Calculate overall risk score for a fraud ring."""
        risk = 0.0
        
        # Factor 1: Network density (tighter = riskier)
        density = nx.density(subgraph)
        risk += density * 30
        
        # Factor 2: Shared device connections (strongest signal)
        shared_device_count = sum(1 for u, v, data in subgraph.edges(data=True)
                                 if data.get('connection_type') == 'shared_device')
        risk += shared_device_count * 10
        
        # Factor 3: Number of players
        risk += len(subgraph.nodes()) * 2
        
        # Factor 4: Average edge weight
        avg_weight = sum(data.get('weight', 1.0) for _, _, data in subgraph.edges(data=True))
        avg_weight = avg_weight / max(subgraph.number_of_edges(), 1)
        risk += avg_weight * 5
        
        return min(risk, 100.0)
    
    def find_communities(self, algorithm: str = 'louvain') -> Dict[str, int]:
        """Detect communities using graph clustering algorithms."""
        try:
            if algorithm == 'louvain':
                # Requires python-louvain package
                import community as community_louvain
                communities = community_louvain.best_partition(self.player_graph)
            elif algorithm == 'greedy':
                communities_gen = nx.community.greedy_modularity_communities(self.player_graph)
                communities = {}
                for idx, comm in enumerate(communities_gen):
                    for player in comm:
                        communities[player] = idx
            else:
                communities = {}
            
            return communities
        except ImportError:
            logger.warning("Community detection library not available")
            return {}
    
    # ===== Centrality Analysis =====
    
    def get_central_players(self, top_n: int = 20) -> List[Tuple[str, float]]:
        """Find most central players (potential fraud ring leaders)."""
        if len(self.player_graph.nodes()) == 0:
            return []
        
        # Degree centrality: highly connected players
        degree_centrality = nx.degree_centrality(self.player_graph)
        
        # Betweenness centrality: players bridging different groups
        betweenness_centrality = nx.betweenness_centrality(self.player_graph)
        
        # Combine scores
        combined_scores = {}
        for player in self.player_graph.nodes():
            combined_scores[player] = (
                degree_centrality.get(player, 0) * 0.6 +
                betweenness_centrality.get(player, 0) * 0.4
            )
        
        # Sort and return top N
        sorted_players = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_players[:top_n]
    
    def get_bridging_accounts(self) -> List[str]:
        """Find accounts that bridge multiple fraud rings."""
        betweenness = nx.betweenness_centrality(self.player_graph)
        
        # High betweenness = bridges communities
        threshold = sorted(betweenness.values(), reverse=True)[min(10, len(betweenness)-1)] if betweenness else 0
        
        bridging_accounts = [player for player, score in betweenness.items() 
                            if score > threshold]
        return bridging_accounts
    
    # ===== Path Analysis =====
    
    def find_connection_path(self, player1: str, player2: str) -> Optional[List[str]]:
        """Find shortest path between two players."""
        try:
            path = nx.shortest_path(self.player_graph, player1, player2)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def get_player_neighborhood(self, player_id: str, depth: int = 2) -> Set[str]:
        """Get all players within N hops of target player."""
        if player_id not in self.player_graph:
            return set()
        
        # BFS to depth N
        visited = set([player_id])
        current_level = {player_id}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                neighbors = set(self.player_graph.neighbors(node))
                next_level.update(neighbors - visited)
            visited.update(next_level)
            current_level = next_level
        
        visited.remove(player_id)  # Remove self
        return visited
    
    # ===== Money Flow Analysis =====
    
    def detect_circular_flows(self) -> List[List[str]]:
        """Detect circular money flows (potential money laundering)."""
        cycles = []
        
        try:
            # Find all simple cycles
            all_cycles = list(nx.simple_cycles(self.transaction_graph))
            
            # Filter cycles with significant total flow
            for cycle in all_cycles:
                if len(cycle) >= 3:  # Minimum 3 players
                    total_flow = 0
                    for i in range(len(cycle)):
                        u = cycle[i]
                        v = cycle[(i + 1) % len(cycle)]
                        if self.transaction_graph.has_edge(u, v):
                            total_flow += self.transaction_graph[u][v].get('total_amount', 0)
                    
                    if total_flow > 1000:  # Threshold
                        cycles.append({
                            'cycle': cycle,
                            'total_flow': total_flow,
                            'length': len(cycle)
                        })
            
            return sorted(cycles, key=lambda x: x['total_flow'], reverse=True)
        
        except Exception as e:
            logger.error(f"Error detecting cycles: {e}")
            return []
    
    # ===== Analytics & Metrics =====
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get overall graph statistics."""
        return {
            'player_graph': {
                'nodes': self.player_graph.number_of_nodes(),
                'edges': self.player_graph.number_of_edges(),
                'density': nx.density(self.player_graph) if self.player_graph.number_of_nodes() > 1 else 0,
                'connected_components': nx.number_connected_components(self.player_graph)
            },
            'device_graph': {
                'nodes': self.device_graph.number_of_nodes(),
                'edges': self.device_graph.number_of_edges()
            },
            'transaction_graph': {
                'nodes': self.transaction_graph.number_of_nodes(),
                'edges': self.transaction_graph.number_of_edges()
            }
        }
    
    def export_for_visualization(self, player_ids: List[str], 
                                output_format: str = 'json') -> Dict[str, Any]:
        """Export subgraph for visualization (D3.js, Gephi, etc.)."""
        subgraph = self.player_graph.subgraph(player_ids)
        
        nodes = []
        for node in subgraph.nodes():
            degree = subgraph.degree(node)
            nodes.append({
                'id': node,
                'degree': degree,
                'size': degree * 2  # For visualization
            })
        
        links = []
        for u, v, data in subgraph.edges(data=True):
            links.append({
                'source': u,
                'target': v,
                'type': data.get('connection_type', 'unknown'),
                'weight': data.get('weight', 1.0)
            })
        
        return {
            'nodes': nodes,
            'links': links
        }
    
    def clear_graphs(self):
        """Clear all graphs (for testing)."""
        self.player_graph.clear()
        self.device_graph.clear()
        self.ip_graph.clear()
        self.transaction_graph.clear()
        self.player_graph = nx.Graph()
        self.device_graph = nx.Graph()
        self.ip_graph = nx.Graph()

    # ===== Analysis Methods =====

    def detect_account_rings(self, player_id: str, max_depth: int = 3) -> Dict:
        """Find all connected accounts in fraud ring."""
        if player_id not in self.player_graph:
            return {'ring_size': 0, 'members': [], 'connections': []}

        # Find all connected nodes
        connected = nx.node_connected_component(self.player_graph, player_id)
        
        # Get subgraph
        ring_graph = self.player_graph.subgraph(connected)
        
        return {
            'ring_size': len(connected),
            'members': list(connected),
            'connections': list(ring_graph.edges()),
            'density': nx.density(ring_graph),
            'avg_degree': sum(dict(ring_graph.degree()).values()) / len(connected) if connected else 0
        }

    def calculate_centrality(self, player_id: str) -> Dict:
        """Calculate centrality scores for suspicious accounts."""
        if player_id not in self.player_graph:
            return {'betweenness': 0, 'closeness': 0, 'degree': 0}
        
        betweenness = nx.betweenness_centrality(self.player_graph)
        closeness = nx.closeness_centrality(self.player_graph)
        degree = dict(self.player_graph.degree())
        
        return {
            'betweenness': betweenness.get(player_id, 0),
            'closeness': closeness.get(player_id, 0),
            'degree': degree.get(player_id, 0)
        }

    def find_communities(self) -> List[Set[str]]:
        """Detect fraud communities using Louvain algorithm."""
        try:
            from networkx.algorithms import community
            communities = community.greedy_modularity_communities(self.player_graph)
            return [set(c) for c in communities]
        except Exception as e:
            logger.error(f"Community detection failed: {e}")
            return []

    def analyze_transaction_flow(self, player_id: str) -> Dict:
        """Analyze money flow patterns for a player."""
        if player_id not in self.transaction_graph:
            return {'total_in': 0, 'total_out': 0, 'connections': 0}
        
        total_in = 0
        total_out = 0
        
        for u, v, data in self.transaction_graph.edges(player_id, data=True):
            amount = data.get('weight', 0)
            if u == player_id:
                total_out += amount
            else:
                total_in += amount
        
        return {
            'total_in': total_in,
            'total_out': total_out,
            'net_flow': total_in - total_out,
            'connections': self.transaction_graph.degree(player_id)
        }

    def detect_circular_flows(self, min_amount: float = 100.0) -> List[List[str]]:
        """Detect circular transaction patterns (money laundering indicator)."""
        cycles = []
        try:
            # Find simple cycles
            for cycle in nx.simple_cycles(self.transaction_graph):
                # Calculate total flow in cycle
                cycle_amount = sum(
                    self.transaction_graph[cycle[i]][cycle[(i+1) % len(cycle)]].get('weight', 0)
                    for i in range(len(cycle))
                )
                if cycle_amount >= min_amount:
                    cycles.append(cycle)
        except Exception as e:
            logger.error(f"Cycle detection failed: {e}")
        
        return cycles

    def get_fraud_score(self, player_id: str) -> float:
        """Calculate overall graph-based fraud score."""
        score = 0.0
        
        # Ring involvement
        ring_data = self.detect_account_rings(player_id)
        if ring_data['ring_size'] > 1:
            score += min(ring_data['ring_size'] * 10, 40)  # Max 40 points
        
        # Centrality (bridging accounts)
        centrality = self.calculate_centrality(player_id)
        score += centrality['betweenness'] * 30  # Max 30 points
        
        # Transaction flow anomalies
        flow = self.analyze_transaction_flow(player_id)
        if flow['net_flow'] < -1000:  # Large net outflow
            score += 20
        
        # Network density
        if player_id in self.player_graph:
            neighbors = list(self.player_graph.neighbors(player_id))
            if len(neighbors) > 5:
                score += 10
        
        return min(score, 100)  # Cap at 100
