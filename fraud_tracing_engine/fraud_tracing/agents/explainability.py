"""
Agent 5: Explainability Agent
Generates human-readable reason strings for every scored node,
ensuring transparency and auditability of fraud decisions.
"""
from typing import Dict, Any, List


# Maps internal flag names → human-readable explanation strings
FLAG_MESSAGES: Dict[str, str] = {
    "sudden_spike":       "High transaction volume spike detected relative to historical average",
    "irregular_timing":   "Irregular and inconsistent transaction timing pattern observed",
    "in_dense_cluster":   "Part of a dense, tightly-connected suspicious transaction cluster",
    "in_cycle":           "Involved in circular fund flows (potential money laundering loop)",
    "is_hub":             "Acts as a high-connectivity hub routing funds to many accounts",
    "high_volume":        "Unusually high total transaction volume compared to network peers",
    "ml_high_risk":       "XGBoost ML model classifies this node as high-risk (>50% fraud probability)",
    "high_frequency":     "Unusually high number of outgoing transactions detected",
    "high_concentration": "Single transaction dominates total outflow volume (potential structuring)",
}

LOW_RISK_MESSAGE = "No significant anomalies detected — consistent with legitimate activity"


class ExplainabilityAgent:
    def generate_reasons(
        self,
        node_scores: Dict[str, Dict[str, Any]],
    ) -> Dict[str, List[str]]:
        """
        Returns: {node_id: [reason_string, ...]}
        """
        reasons: Dict[str, List[str]] = {}

        for node, score_data in node_scores.items():
            active_flags: List[str] = score_data.get("active_flags", [])
            node_reasons: List[str] = []

            for flag in active_flags:
                msg = FLAG_MESSAGES.get(flag)
                if msg:
                    node_reasons.append(msg)

            if not node_reasons:
                node_reasons.append(LOW_RISK_MESSAGE)

            reasons[node] = node_reasons

        return reasons
