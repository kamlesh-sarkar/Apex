"""
Agent 1: Behavioral Analysis Agent (Enhanced with ML Feature Engineering)
Analyzes per-node transaction patterns to detect anomalies including:
- Sudden volume spikes (z-score based)
- Irregular timing patterns (coefficient of variation)
- Transaction frequency analysis
- Unique counterparty analysis
- Volume concentration ratios
- Net flow imbalance detection

Feature engineering techniques adapted from the Antimoney XGBoost pipeline.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any


class BehavioralAnalysisAgent:
    def __init__(self, spike_z_threshold: float = 2.0):
        """
        spike_z_threshold: how many standard deviations above the mean
        constitutes a 'sudden spike' in transaction amounts.
        """
        self.spike_z_threshold = spike_z_threshold

    def analyze(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Returns per-node behavioral flags dict with enhanced features:
        {
          node_id: {
            "sudden_spike": bool,
            "irregular_timing": bool,
            "tx_count": int,
            "total_volume": float,
            "is_stable": bool,
            # ── New ML-grade features ──
            "tx_in_count": int,
            "total_received": float,
            "mean_sent": float,
            "std_sent": float,
            "max_sent": float,
            "max_zscore": float,
            "unique_receivers": int,
            "unique_senders": int,
            "concentration": float,
            "net_flow_ratio": float,
            "timing_cv": float,
            "high_frequency": bool,
            "high_concentration": bool,
          }
        }
        """
        behavioral_flags: Dict[str, Dict[str, Any]] = {}

        # Collect all nodes present
        all_nodes = set(df["sender"].unique()) | set(df["receiver"].unique())

        for node in all_nodes:
            # Transactions where this node is the SENDER (active behavior)
            sent_df = df[df["sender"] == node].copy()
            recv_df = df[df["receiver"] == node]

            tx_count = len(sent_df)
            tx_in_count = len(recv_df)
            total_volume = float(sent_df["amount"].sum()) if tx_count > 0 else 0.0
            total_received = float(recv_df["amount"].sum()) if tx_in_count > 0 else 0.0

            sudden_spike = False
            irregular_timing = False
            timing_cv = 0.0

            # ── Amount statistics ────────────────────────────────────────
            mean_sent = float(sent_df["amount"].mean()) if tx_count > 0 else 0.0
            std_sent = float(sent_df["amount"].std()) if tx_count >= 2 else 0.0
            max_sent = float(sent_df["amount"].max()) if tx_count > 0 else 0.0

            # Z-score of max transaction (anomaly strength signal)
            max_zscore = ((max_sent - mean_sent) / std_sent) if std_sent > 0 else 0.0

            if tx_count >= 2:
                amounts = sent_df["amount"].values
                mean_amt = amounts.mean()
                std_amt = amounts.std()

                # Sudden spike: last transaction amount significantly above mean
                last_amt = amounts[-1]
                if std_amt > 0 and (last_amt - mean_amt) / std_amt > self.spike_z_threshold:
                    sudden_spike = True

                # Irregular timing: high coefficient of variation in inter-tx intervals
                if "timestamp" in sent_df.columns:
                    sent_df = sent_df.sort_values("timestamp")
                    deltas = sent_df["timestamp"].diff().dropna().dt.total_seconds().abs()
                    if len(deltas) > 0 and deltas.mean() > 0:
                        cv = float(deltas.std() / deltas.mean())
                        timing_cv = cv
                        # CV > 1.0 indicates very irregular timing
                        irregular_timing = bool(cv > 1.0)

            # ── Unique counterparties ────────────────────────────────────
            unique_receivers = int(sent_df["receiver"].nunique()) if tx_count > 0 else 0
            unique_senders = int(recv_df["sender"].nunique()) if tx_in_count > 0 else 0

            # ── Volume concentration (max single txn / total volume) ─────
            concentration = (max_sent / total_volume) if total_volume > 0 else 0.0

            # ── Net flow ratio: (sent - received) / (sent + received) ────
            total_flow = total_volume + total_received
            net_flow_ratio = (total_volume - total_received) / total_flow if total_flow > 0 else 0.0

            # ── Derived boolean flags (for risk scoring) ─────────────────
            # High frequency: 4+ outgoing transactions
            high_frequency = tx_count >= 4

            # High concentration: single txn is >60% of total volume
            high_concentration = concentration > 0.6 and tx_count >= 2

            # A node is considered "stable" if it has consistent, non-spiking behavior
            is_stable = (
                (not sudden_spike)
                and (not irregular_timing)
                and (not high_frequency)
                and (tx_count > 0)
            )

            behavioral_flags[node] = {
                "sudden_spike": sudden_spike,
                "irregular_timing": irregular_timing,
                "tx_count": tx_count,
                "total_volume": total_volume,
                "is_stable": is_stable,
                # ── New ML-grade features ──
                "tx_in_count": tx_in_count,
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
                "high_frequency": high_frequency,
                "high_concentration": high_concentration,
            }

        return behavioral_flags
