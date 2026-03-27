"""
Agent 3: Risk Scoring Agent (Hybrid: Rule-Based + ML)
Combines behavioral flags, network flags, AND XGBoost ML predictions
into a weighted risk score per node.

Graph-based rules (cycles, hubs, clusters) are PRESERVED.
ML predictions are added as an extra high-weight signal.
"""
import networkx as nx
from typing import Dict, Any, Optional


# ── Rule-based scoring weights (UNCHANGED) ───────────────────────────────
WEIGHT_SUDDEN_SPIKE       = 30
WEIGHT_IRREGULAR_TIMING   = 20
WEIGHT_IN_DENSE_CLUSTER   = 30  # hub in dense cluster = key fraud indicator
WEIGHT_IN_CYCLE           = 20
WEIGHT_IS_HUB             = 25  # fan-out hub = strong kingpin signal
WEIGHT_HIGH_VOLUME        = 10

# ── NEW: ML + enhanced behavioral weights ────────────────────────────────
WEIGHT_ML_PREDICTION      = 40  # XGBoost says fraud → strongest signal
WEIGHT_HIGH_FREQUENCY     = 15  # 4+ outgoing transactions
WEIGHT_HIGH_CONCENTRATION = 15  # single txn dominates total volume

# Risk label thresholds
THRESHOLD_HIGH   = 60  # hub + dense + high_volume = 65 → High
THRESHOLD_MEDIUM = 25  # dense cluster alone → Medium


class RiskScoringAgent:
    def __init__(self, high_volume_percentile: float = 0.80):
        """
        high_volume_percentile: nodes in the top X% by total sent volume
                                receive the high_volume bonus.
        """
        self.high_volume_percentile = high_volume_percentile

    def score(
        self,
        behavioral_flags: Dict[str, Dict[str, Any]],
        network_flags: Dict[str, Dict[str, Any]],
        ml_predictions: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Returns per-node risk output:
        {
          node_id: {
            "score": int (0-100+),
            "label": "Low" | "Medium" | "High",
            "is_fraud": bool,
            "active_flags": [str, ...],
            "fraud_probability": float  # from ML model (0.0-1.0)
          }
        }
        """
        if ml_predictions is None:
            ml_predictions = {}

        all_nodes = set(behavioral_flags.keys()) | set(network_flags.keys())

        # Determine high-volume threshold across all nodes
        volumes = [
            behavioral_flags[n].get("total_volume", 0.0)
            for n in all_nodes
            if n in behavioral_flags
        ]
        if volumes:
            sorted_vols = sorted(volumes)
            cutoff_idx = int(len(sorted_vols) * self.high_volume_percentile)
            high_volume_cutoff = sorted_vols[max(cutoff_idx - 1, 0)]
        else:
            high_volume_cutoff = float("inf")

        node_scores: Dict[str, Dict[str, Any]] = {}

        for node in all_nodes:
            b = behavioral_flags.get(node, {})
            n = network_flags.get(node, {})
            ml = ml_predictions.get(node, {})

            raw_score = 0
            active_flags = []

            # ── Original rule-based flags (PRESERVED) ────────────────────
            if b.get("sudden_spike", False):
                raw_score += WEIGHT_SUDDEN_SPIKE
                active_flags.append("sudden_spike")

            if b.get("irregular_timing", False):
                raw_score += WEIGHT_IRREGULAR_TIMING
                active_flags.append("irregular_timing")

            if n.get("in_dense_cluster", False):
                raw_score += WEIGHT_IN_DENSE_CLUSTER
                active_flags.append("in_dense_cluster")

            if n.get("in_cycle", False):
                raw_score += WEIGHT_IN_CYCLE
                active_flags.append("in_cycle")

            if n.get("is_hub", False):
                raw_score += WEIGHT_IS_HUB
                active_flags.append("is_hub")

            if b.get("total_volume", 0.0) >= high_volume_cutoff and b.get("total_volume", 0.0) > 0:
                raw_score += WEIGHT_HIGH_VOLUME
                active_flags.append("high_volume")

            # ── NEW: Enhanced behavioral flags ───────────────────────────
            if b.get("high_frequency", False):
                raw_score += WEIGHT_HIGH_FREQUENCY
                active_flags.append("high_frequency")

            if b.get("high_concentration", False):
                raw_score += WEIGHT_HIGH_CONCENTRATION
                active_flags.append("high_concentration")

            # ── NEW: ML prediction signal ────────────────────────────────
            fraud_probability = ml.get("fraud_probability", 0.0)
            if fraud_probability > 0.5:
                raw_score += WEIGHT_ML_PREDICTION
                active_flags.append("ml_high_risk")

            # Cap at 100
            raw_score = min(raw_score, 100)

            if raw_score >= THRESHOLD_HIGH:
                label = "High"
                is_fraud = True
            elif raw_score >= THRESHOLD_MEDIUM:
                label = "Medium"
                is_fraud = False  # Medium = suspicious, not conclusive
            else:
                label = "Low"
                is_fraud = False

            node_scores[node] = {
                "score": raw_score,
                "label": label,
                "is_fraud": is_fraud,
                "active_flags": active_flags,
                "fraud_probability": fraud_probability,
            }

        return node_scores

