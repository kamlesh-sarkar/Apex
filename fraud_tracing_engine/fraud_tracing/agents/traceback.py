"""
Agent 4: Traceback Validation Agent
Traces fraudulent origins of a suspicious node, filtering intermediate
nodes using risk scores so that innocent pass-through nodes are excluded.
"""
import networkx as nx
from typing import List, Dict, Any

# Only nodes at or above this label are considered suspicious ancestors
SUSPICIOUS_LABELS = {"Medium", "High"}
# Maximum number of paths to enumerate (keeps it lightweight)
MAX_PATHS = 20


class TracebackAgent:
    def trace_origins(
        self,
        G: nx.DiGraph,
        suspicious_node: str,
        node_scores: Dict[str, Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Traces origins of fraudulent activity.

        Parameters
        ----------
        G : nx.DiGraph  — full transaction graph
        suspicious_node : str  — target node to trace from
        node_scores : dict  — output from RiskScoringAgent (optional).
                              When provided, only Medium/High risk ancestors
                              are included, preventing innocent nodes from
                              being labeled as fraudulent.

        Returns
        -------
        {
          "ancestors": [str, ...],          # filtered ancestor list
          "suspicious_edges": [(u, v, d)],  # edges in suspicious subgraph
          "suspicious_subgraph": nx.DiGraph,
          "trace_paths": [[str, ...], ...]  # short paths from root to target
        }
        """
        if suspicious_node not in G:
            return {"error": f"Node '{suspicious_node}' not found in graph."}

        # All nodes that can reach the suspicious node
        raw_ancestors: List[str] = list(nx.ancestors(G, suspicious_node))

        # --- Filter ancestors by risk score (Agent 4 validation logic) ---
        if node_scores:
            filtered_ancestors = [
                n for n in raw_ancestors
                if node_scores.get(n, {}).get("label", "Low") in SUSPICIOUS_LABELS
            ]
        else:
            filtered_ancestors = raw_ancestors

        # Build subgraph from suspicious ancestors + the target
        subgraph_nodes = set(filtered_ancestors) | {suspicious_node}
        suspicious_subgraph = G.subgraph(subgraph_nodes).copy()
        suspicious_edges = list(suspicious_subgraph.edges(data=True))

        # --- Enumerate trace paths (lightweight, capped) ---
        trace_paths: List[List[str]] = []
        source_candidates = [n for n in filtered_ancestors
                             if suspicious_subgraph.in_degree(n) == 0]

        if not source_candidates:
            source_candidates = filtered_ancestors[:5]  # fallback

        for source in source_candidates:
            try:
                for path in nx.all_simple_paths(
                    suspicious_subgraph, source=source, target=suspicious_node, cutoff=8
                ):
                    trace_paths.append(path)
                    if len(trace_paths) >= MAX_PATHS:
                        break
            except nx.NetworkXError:
                pass
            if len(trace_paths) >= MAX_PATHS:
                break

        return {
            "ancestors": filtered_ancestors,
            "suspicious_edges": suspicious_edges,
            "suspicious_subgraph": suspicious_subgraph,
            "trace_paths": trace_paths,
        }
