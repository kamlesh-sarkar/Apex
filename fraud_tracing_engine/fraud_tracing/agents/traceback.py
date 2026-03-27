import networkx as nx
from typing import List, Dict, Any

class TracebackAgent:
    def __init__(self):
        pass

    def trace_origins(self, G: nx.DiGraph, suspicious_node: str) -> Dict[str, Any]:
        """
        Traces the origins of fraudulent activity by finding all ancestors of the suspicious node,
        and all simple paths from those ancestors to the suspicious node.
        """
        if suspicious_node not in G:
            return {"error": f"Node {suspicious_node} not in graph."}

        # Find all nodes that can reach the suspicious node
        ancestors = list(nx.ancestors(G, suspicious_node))
        
        # Create a subgraph of just the ancestors and the suspicious node for further analysis
        subgraph_nodes = set(ancestors)
        subgraph_nodes.add(suspicious_node)
        suspicious_subgraph = G.subgraph(subgraph_nodes)
        
        # Instead of exponential pathfinding, extract edges to represent flow route
        suspicious_edges = list(suspicious_subgraph.edges(data=True))

        return {
            "ancestors": ancestors,
            "suspicious_edges": suspicious_edges,
            "suspicious_subgraph": suspicious_subgraph
        }
