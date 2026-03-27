import networkx as nx
from typing import Optional

class KingpinDetectionAgent:
    def __init__(self):
        pass

    def identify_kingpin(self, suspicious_subgraph: nx.DiGraph, fraud_node: str) -> Optional[str]:
        """
        Identifies the 'kingpin' or origin node of the fraud network.
        Uses out-degree centrality (who sends to the most distinct nodes in the suspicious network)
        and betweenness centrality as a tiebreaker.
        """
        if len(suspicious_subgraph) <= 1:
            return None
            
        # Ignore the target fraud_node itself when looking for the originator
        candidates = [n for n in suspicious_subgraph.nodes if n != fraud_node]
        if not candidates:
            return None

        # Primary signal: out-degree centrality — O(V+E), measures who sends to the most nodes
        out_degree_centrality = nx.out_degree_centrality(suspicious_subgraph)
        
        # Tiebreaker: in-degree centrality — also O(V+E), avoids the expensive betweenness O(VE) call
        in_degree_centrality = nx.in_degree_centrality(suspicious_subgraph)
        
        # Kingpin = highest out-degree (spreads money to most nodes). Tiebreak on in-degree.
        kingpin = max(candidates, key=lambda n: (out_degree_centrality[n], in_degree_centrality[n]))
        
        return kingpin
