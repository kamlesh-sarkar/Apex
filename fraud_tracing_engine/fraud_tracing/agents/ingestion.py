import pandas as pd
from typing import Optional


class DataIngestionAgent:
    def __init__(self, project_id: Optional[str] = None, use_mock: bool = False):
        self.project_id = project_id
        self.use_mock = use_mock
        if not self.use_mock:
            from google.cloud import bigquery
            self.client = bigquery.Client(project=project_id)

    def fetch_transactions(self, query: Optional[str] = None) -> pd.DataFrame:
        if self.use_mock:
            return self._get_mock_data()

        if not query:
            raise ValueError("Query must be provided if not using mock data")

        query_job = self.client.query(query)
        df = query_job.to_dataframe()
        return df

    def _get_mock_data(self) -> pd.DataFrame:
        """
        Returns rich mock transaction data including:
        - A clear fraud ring: K1 -> I* -> F1 (dense cluster, high volume)
        - A circular money-laundering loop: I9 -> I10 -> I11 -> I9
        - Legitimate high-volume business node: B1 (consistent, non-suspicious)
        - Passive noise nodes: N1, N2, N3 (small amounts, isolated)
        Timestamps spread over hours to give behavioral analysis material to work with.
        """
        data = [
            # ── Fraud ring: Kingpin distributes ──────────────────────────
            ("K1", "I1", 5000, "2024-01-01T10:00:00Z"),
            ("K1", "I2", 4000, "2024-01-01T10:05:00Z"),
            ("K1", "I3", 6000, "2024-01-01T10:10:00Z"),

            # ── Intermediary layer 1 ──────────────────────────────────────
            ("I1", "I4", 2500, "2024-01-01T11:00:00Z"),
            ("I1", "I5", 2500, "2024-01-01T11:05:00Z"),
            ("I2", "I6", 4000, "2024-01-01T11:10:00Z"),
            ("I3", "I7", 3000, "2024-01-01T11:15:00Z"),
            ("I3", "I8", 3000, "2024-01-01T11:20:00Z"),

            # ── Final layer funneling to the known fraud node ─────────────
            ("I4", "F1", 2500, "2024-01-01T12:00:00Z"),
            ("I5", "F1", 2500, "2024-01-01T12:05:00Z"),
            ("I6", "F1", 4000, "2024-01-01T12:10:00Z"),
            ("I7", "F1", 3000, "2024-01-01T12:15:00Z"),
            ("I8", "F1", 3000, "2024-01-01T12:20:00Z"),

            # ── Circular flow (money laundering loop) ─────────────────────
            ("I9",  "I10", 1500, "2024-01-01T13:00:00Z"),
            ("I10", "I11", 1500, "2024-01-01T13:30:00Z"),
            ("I11", "I9",  1500, "2024-01-01T14:00:00Z"),

            # ── Legitimate business node: regular, consistent payments ─────
            ("B1", "V1", 10000, "2024-01-01T08:00:00Z"),
            ("B1", "V2", 10000, "2024-01-02T08:00:00Z"),
            ("B1", "V3", 10000, "2024-01-03T08:00:00Z"),
            ("B1", "V4", 10000, "2024-01-04T08:00:00Z"),

            # ── Passive noise nodes (small, isolated) ─────────────────────
            ("N1", "N2", 100, "2024-01-01T09:00:00Z"),
            ("N2", "N3", 100, "2024-01-01T09:15:00Z"),
        ]
        df = pd.DataFrame(data, columns=["sender", "receiver", "amount", "timestamp"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
