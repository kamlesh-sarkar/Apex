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

        # Calculate out-degree centrality (normalized out-degree)
        out_degree_centrality = nx.out_degree_centrality(suspicious_subgraph)
        
        # We can also calculate betweenness just to have it
        betweenness = nx.betweenness_centrality(suspicious_subgraph)
        
        # A true orchestrator might have no incoming edges in this context (in-degree 0) 
        # but a high out-degree.
        
        # Score = Out-Degree Centrality. If tie, Betweenness Centrality.
        kingpin = max(candidates, key=lambda n: (out_degree_centrality[n], betweenness[n]))
        
        return kingpin
