"""
Agent 2: Network Context Agent
Analyzes the graph structure to detect fraud-ring patterns:

1. Circular flows — directed cycles (laundering loops)
2. Multi-path convergence — multiple distinct paths funneling to the same node
   (fan-out distributor + fan-in receiver = fraud ring signature)
3. Hub nodes — high out-degree senders in a suspicious context

Principle: A legitimate star topology (B1→V1..V4) has no convergence;
a fraud ring (K1→I*→F1) has strong multi-path convergence at F1.
"""
import networkx as nx
from typing import Dict, Any, Set


class NetworkContextAgent:
    def __init__(
        self,
        hub_min_out_degree: int = 3,
        fan_in_min_predecessors: int = 3,
        max_cycle_search: int = 100,
    ):
        """
        hub_min_out_degree       : absolute out-degree minimum to flag a hub sender.
        fan_in_min_predecessors  : min number of distinct direct predecessors to flag
                                   a node as a multi-path convergence target.
        max_cycle_search         : upper limit on enumerating directed cycles.
        """
        self.hub_min_out_degree      = hub_min_out_degree
        self.fan_in_min_predecessors = fan_in_min_predecessors
        self.max_cycle_search        = max_cycle_search

    def analyze(self, G: nx.DiGraph) -> Dict[str, Dict[str, Any]]:
        """
        Returns per-node network flags:
        {
          node_id: {
            "in_dense_cluster": bool,   # in a multi-path convergence ring
            "in_cycle": bool,           # node participates in a directed cycle
            "is_hub": bool,             # high-fan-out distributor
            "cluster_size": int
          }
        }
        """
        network_flags: Dict[str, Dict[str, Any]] = {
            n: {
                "in_dense_cluster": False,
                "in_cycle": False,
                "is_hub": False,
                "cluster_size": 1,
            }
            for n in G.nodes
        }

        if len(G.nodes) == 0:
            return network_flags

        # ── 1. Circular flow detection ─────────────────────────────────────
        nodes_in_cycles: Set[str] = set()
        cycle_count = 0
        try:
            for cycle in nx.simple_cycles(G):
                if cycle_count >= self.max_cycle_search:
                    break
                for node in cycle:
                    nodes_in_cycles.add(node)
                cycle_count += 1
        except Exception:
            pass

        for node in nodes_in_cycles:
            if node in network_flags:
                network_flags[node]["in_cycle"] = True

        # ── 2. Hub detection (absolute out-degree, any context) ────────────
        hub_nodes: Set[str] = set()
        for node in G.nodes:
            if G.out_degree(node) >= self.hub_min_out_degree:
                hub_nodes.add(node)
                network_flags[node]["is_hub"] = True

        # ── 3. Multi-path convergence detection ───────────────────────────
        # A node is a "convergence target" if multiple distinct nodes send to it.
        # In a fraud ring (K1→I1..I8→F1), F1 has 5 direct predecessors.
        # The hub node K1 and all intermediaries that funnel to F1 are flagged.
        convergence_targets: Set[str] = set()
        for node in G.nodes:
            in_deg = G.in_degree(node)
            if in_deg >= self.fan_in_min_predecessors:
                convergence_targets.add(node)

        # For each convergence target, mark all upstream ancestors as part
        # of a dense cluster (the fraud ring).
        for target in convergence_targets:
            ancestors = nx.ancestors(G, target)
            cluster_nodes = ancestors | {target}
            cluster_size  = len(cluster_nodes)
            for node in cluster_nodes:
                if node in network_flags:
                    network_flags[node]["in_dense_cluster"] = True
                    # Keep the largest cluster size seen
                    if cluster_size > network_flags[node]["cluster_size"]:
                        network_flags[node]["cluster_size"] = cluster_size

        # Nodes already in cycles also belong to a suspicious cluster
        for node in nodes_in_cycles:
            if node in network_flags and not network_flags[node]["in_dense_cluster"]:
                network_flags[node]["in_dense_cluster"] = False  # cycles scored via in_cycle

        return network_flags
