import json
from typing import Dict, Any, List, Optional


class OutputFormatterAgent:
    def format_output(
        self,
        fraud_node: str,
        kingpin: str,
        node_scores: Dict[str, Dict[str, Any]],
        reasons: Dict[str, List[str]],
        suspicious_edges: List[tuple],
        trace_paths: List[List[str]],
        ml_predictions: Optional[Dict[str, Dict[str, Any]]] = None,
        ml_metrics: Optional[Dict[str, Any]] = None,
        evaluation_report: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Formats the enriched fraud analysis results into a JSON string.
        Now includes ML prediction data, model metrics, and evaluation report.

        Output schema:
        {
          "node": str,
          "risk_score": str,        # "Low" | "Medium" | "High"
          "risk_score_value": int,  # 0-100 numeric
          "is_fraud": bool,
          "fraud_probability": float,  # ML model probability
          "reasons": [str, ...],
          "kingpin": str,
          "trace_paths": [[str, ...], ...],
          "suspicious_edges": [{source, target, amount, tx_count}, ...],
          "all_node_scores": {node: {score, label, is_fraud, fraud_probability, reasons}, ...},
          "ml_metrics": {auc_roc, precision, recall, f1_score, ...},
          "evaluation_report": {model_performance, scoring_analysis, roc_curve_points, ...}
        }
        """
        if ml_predictions is None:
            ml_predictions = {}
        if ml_metrics is None:
            ml_metrics = {}
        if evaluation_report is None:
            evaluation_report = {}

        target_score = node_scores.get(fraud_node, {})
        target_ml = ml_predictions.get(fraud_node, {})

        formatted_edges = [
            {
                "source": u,
                "target": v,
                "amount": d.get("amount", 0),
                "tx_count": d.get("tx_count", 1),
                "timestamps": [str(ts) for ts in d.get("timestamps", [])],
            }
            for u, v, d in suspicious_edges
        ]

        # Build a compact summary for every scored node
        all_node_scores = {
            node: {
                "score": data.get("score", 0),
                "label": data.get("label", "Low"),
                "is_fraud": data.get("is_fraud", False),
                "fraud_probability": data.get("fraud_probability", 0.0),
                "ml_prediction": ml_predictions.get(node, {}).get("ml_prediction", "unknown"),
                "reasons": reasons.get(node, []),
            }
            for node, data in node_scores.items()
        }

        output_dict = {
            # ── Primary target ──────────────────────────────────────────
            "node": fraud_node,
            "risk_score": target_score.get("label", "Low"),
            "risk_score_value": target_score.get("score", 0),
            "is_fraud": target_score.get("is_fraud", False),
            "fraud_probability": target_ml.get("fraud_probability", 0.0),
            "reasons": reasons.get(fraud_node, []),
            # ── Fraud network ────────────────────────────────────────────
            "kingpin": kingpin,
            "trace_paths": trace_paths,
            "suspicious_edges": formatted_edges,
            # ── Full network analysis ─────────────────────────────────────
            "all_node_scores": all_node_scores,
            # ── ML Model Performance ──────────────────────────────────────
            "ml_metrics": ml_metrics,
            # ── Evaluation Report (ROC, confusion matrix, etc.) ───────────
            "evaluation_report": evaluation_report,
        }

        return json.dumps(output_dict, indent=2, default=str)

