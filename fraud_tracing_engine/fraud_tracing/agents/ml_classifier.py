"""
Agent: ML Classifier Agent (XGBoost)
Trains a gradient-boosted tree model on transaction features to produce
per-node fraud probability scores. Integrates with the existing graph-based
pipeline — does NOT replace it, but adds a learned signal.

Uses mock labeled data for training in hackathon/demo mode.
For production: load a pre-trained model from a .pkl file.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, confusion_matrix, classification_report


class MLClassifierAgent:
    def __init__(self):
        self.model: Optional[XGBClassifier] = None
        self.feature_columns = []
        self.metrics: Dict[str, Any] = {}

    # ── Feature Engineering ──────────────────────────────────────────────
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms raw transaction DataFrame into per-node ML features.
        Borrows techniques from the Antimoney project:
          - Amount statistics (mean, std, max, z-score)
          - Transaction frequency
          - Unique counterparties
          - Volume concentration ratio
        """
        all_nodes = set(df["sender"].unique()) | set(df["receiver"].unique())
        features = []

        for node in all_nodes:
            sent = df[df["sender"] == node]
            received = df[df["receiver"] == node]

            tx_out_count = len(sent)
            tx_in_count = len(received)
            total_sent = float(sent["amount"].sum()) if tx_out_count > 0 else 0.0
            total_received = float(received["amount"].sum()) if tx_in_count > 0 else 0.0

            # Amount statistics (sent)
            mean_sent = float(sent["amount"].mean()) if tx_out_count > 0 else 0.0
            std_sent = float(sent["amount"].std()) if tx_out_count >= 2 else 0.0
            max_sent = float(sent["amount"].max()) if tx_out_count > 0 else 0.0

            # Z-score of max transaction (anomaly signal)
            max_zscore = ((max_sent - mean_sent) / std_sent) if std_sent > 0 else 0.0

            # Unique counterparties
            unique_receivers = sent["receiver"].nunique() if tx_out_count > 0 else 0
            unique_senders = received["sender"].nunique() if tx_in_count > 0 else 0

            # Volume concentration: max single txn / total volume
            concentration = (max_sent / total_sent) if total_sent > 0 else 0.0

            # Net flow ratio: (sent - received) / (sent + received)
            total_flow = total_sent + total_received
            net_flow_ratio = (total_sent - total_received) / total_flow if total_flow > 0 else 0.0

            # Timing features
            timing_cv = 0.0
            if tx_out_count >= 2 and "timestamp" in sent.columns:
                sorted_sent = sent.sort_values("timestamp")
                deltas = sorted_sent["timestamp"].diff().dropna().dt.total_seconds().abs()
                if len(deltas) > 0 and deltas.mean() > 0:
                    timing_cv = float(deltas.std() / deltas.mean())

            features.append({
                "node": node,
                "tx_out_count": tx_out_count,
                "tx_in_count": tx_in_count,
                "total_sent": total_sent,
                "total_received": total_received,
                "mean_sent": mean_sent,
                "std_sent": std_sent,
                "max_sent": max_sent,
                "max_zscore": max_zscore,
                "unique_receivers": unique_receivers,
                "unique_senders": unique_senders,
                "concentration": concentration,
                "net_flow_ratio": net_flow_ratio,
                "timing_cv": timing_cv,
            })

        return pd.DataFrame(features)

    # ── Generate labeled training data (hackathon mock) ──────────────────
    def _generate_training_data(self) -> pd.DataFrame:
        """
        Generates synthetic labeled transaction data for XGBoost training.
        Labels are based on known fraud patterns (rings, high-volume splits).
        In production, this would be replaced by historical labeled data.
        """
        np.random.seed(42)
        records = []

        # ── Fraud ring pattern (20 samples) ─────────────────────────────
        for i in range(20):
            records.append({
                "node": f"FRAUD_{i}",
                "tx_out_count": np.random.randint(3, 8),
                "tx_in_count": np.random.randint(3, 8),
                "total_sent": np.random.uniform(8000, 25000),
                "total_received": np.random.uniform(8000, 25000),
                "mean_sent": np.random.uniform(2000, 5000),
                "std_sent": np.random.uniform(800, 2000),
                "max_sent": np.random.uniform(5000, 10000),
                "max_zscore": np.random.uniform(1.5, 4.0),
                "unique_receivers": np.random.randint(3, 8),
                "unique_senders": np.random.randint(3, 8),
                "concentration": np.random.uniform(0.3, 0.6),
                "net_flow_ratio": np.random.uniform(-0.3, 0.3),
                "timing_cv": np.random.uniform(0.8, 2.5),
                "is_fraud": 1,
            })

        # ── Legitimate pattern (40 samples) ─────────────────────────────
        for i in range(40):
            records.append({
                "node": f"LEGIT_{i}",
                "tx_out_count": np.random.randint(1, 5),
                "tx_in_count": np.random.randint(1, 5),
                "total_sent": np.random.uniform(500, 8000),
                "total_received": np.random.uniform(500, 8000),
                "mean_sent": np.random.uniform(500, 2000),
                "std_sent": np.random.uniform(50, 500),
                "max_sent": np.random.uniform(1000, 4000),
                "max_zscore": np.random.uniform(0.0, 1.2),
                "unique_receivers": np.random.randint(1, 4),
                "unique_senders": np.random.randint(1, 4),
                "concentration": np.random.uniform(0.5, 1.0),
                "net_flow_ratio": np.random.uniform(-0.5, 0.5),
                "timing_cv": np.random.uniform(0.0, 0.7),
                "is_fraud": 0,
            })

        return pd.DataFrame(records)

    # ── Train ────────────────────────────────────────────────────────────
    def train(self):
        """
        Trains XGBoost classifier on synthetic labeled data.
        Stores evaluation metrics (AUC, confusion matrix) for presentation.
        """
        train_df = self._generate_training_data()

        self.feature_columns = [
            "tx_out_count", "tx_in_count", "total_sent", "total_received",
            "mean_sent", "std_sent", "max_sent", "max_zscore",
            "unique_receivers", "unique_senders", "concentration",
            "net_flow_ratio", "timing_cv",
        ]

        X = train_df[self.feature_columns].values
        y = train_df["is_fraud"].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y,
        )

        self.model = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
        )
        self.model.fit(X_train, y_train)

        # ── Evaluation metrics ───────────────────────────────────────────
        y_proba = self.model.predict_proba(X_test)[:, 1]
        y_pred = self.model.predict(X_test)
        auc = roc_auc_score(y_test, y_proba)
        cm = confusion_matrix(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)

        self.metrics = {
            "auc_roc": round(auc, 4),
            "confusion_matrix": {
                "true_negatives": int(cm[0][0]),
                "false_positives": int(cm[0][1]),
                "false_negatives": int(cm[1][0]),
                "true_positives": int(cm[1][1]),
            },
            "precision": round(report.get("1", {}).get("precision", 0), 4),
            "recall": round(report.get("1", {}).get("recall", 0), 4),
            "f1_score": round(report.get("1", {}).get("f1-score", 0), 4),
            "accuracy": round(report.get("accuracy", 0), 4),
        }

        # Feature importance for explainability
        importances = self.model.feature_importances_
        self.metrics["feature_importance"] = {
            name: round(float(imp), 4)
            for name, imp in sorted(
                zip(self.feature_columns, importances),
                key=lambda x: x[1],
                reverse=True,
            )
        }

        return self.metrics

    # ── Predict ──────────────────────────────────────────────────────────
    def predict(
        self,
        df: pd.DataFrame,
        precomputed_features: Dict[str, Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Runs the trained XGBoost model on live transaction data.

        If precomputed_features (from BehavioralAnalysisAgent) is provided,
        reuses those features instead of recomputing from scratch — ~2x faster.

        Returns per-node ML predictions:
        {
            node: {
                "fraud_probability": float (0.0-1.0),
                "ml_prediction": "fraud" | "legitimate",
                "ml_confidence": float
            }
        }
        """
        if self.model is None:
            self.train()

        if precomputed_features:
            # Reuse features already computed by BehavioralAnalysisAgent
            features_df = self._features_from_behavioral(precomputed_features)
        else:
            # Fallback: compute from raw transactions (slower)
            features_df = self._engineer_features(df)

        nodes = features_df["node"].tolist()
        X = features_df[self.feature_columns].values

        probabilities = self.model.predict_proba(X)[:, 1]

        ml_predictions: Dict[str, Dict[str, Any]] = {}
        for node, prob in zip(nodes, probabilities):
            ml_predictions[node] = {
                "fraud_probability": round(float(prob), 4),
                "ml_prediction": "fraud" if prob > 0.5 else "legitimate",
                "ml_confidence": round(float(max(prob, 1 - prob)), 4),
            }

        return ml_predictions

    def _features_from_behavioral(
        self, behavioral_flags: Dict[str, Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Converts BehavioralAnalysisAgent output into the feature DataFrame
        format expected by XGBoost — avoids recomputing identical stats.
        """
        records = []
        for node, flags in behavioral_flags.items():
            records.append({
                "node": node,
                "tx_out_count": flags.get("tx_count", 0),
                "tx_in_count": flags.get("tx_in_count", 0),
                "total_sent": flags.get("total_volume", 0.0),
                "total_received": flags.get("total_received", 0.0),
                "mean_sent": flags.get("mean_sent", 0.0),
                "std_sent": flags.get("std_sent", 0.0),
                "max_sent": flags.get("max_sent", 0.0),
                "max_zscore": flags.get("max_zscore", 0.0),
                "unique_receivers": flags.get("unique_receivers", 0),
                "unique_senders": flags.get("unique_senders", 0),
                "concentration": flags.get("concentration", 0.0),
                "net_flow_ratio": flags.get("net_flow_ratio", 0.0),
                "timing_cv": flags.get("timing_cv", 0.0),
            })
        return pd.DataFrame(records)

    def get_metrics(self) -> Dict[str, Any]:
        """Returns stored evaluation metrics for API/presentation."""
        return self.metrics
