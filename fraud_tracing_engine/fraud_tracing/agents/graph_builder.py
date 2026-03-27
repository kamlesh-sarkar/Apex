import networkx as nx
import pandas as pd
from typing import Dict, Any


class GraphConstructionAgent:
    def build_graph(self, transactions_df: pd.DataFrame) -> nx.DiGraph:
        """
        Converts a transactions DataFrame to a directed weighted graph.
        
        Nodes: Accounts (senders / receivers)
        Edges: Transaction flows
        Edge attributes:
          - amount: cumulative transfer amount
          - timestamps: list of all transaction datetimes (for behavioral analysis)
          - tx_count: number of individual transactions on this edge
        """
        G = nx.DiGraph()

        # itertuples is 5-10x faster than iterrows for DataFrame iteration
        for row in transactions_df.itertuples(index=False):
            sender    = row.sender
            receiver  = row.receiver
            amount    = row.amount
            timestamp = row.timestamp

            if G.has_edge(sender, receiver):
                G[sender][receiver]["amount"]     += amount
                G[sender][receiver]["timestamps"].append(timestamp)
                G[sender][receiver]["tx_count"]   += 1
            else:
                G.add_edge(
                    sender,
                    receiver,
                    amount=amount,
                    timestamps=[timestamp],
                    tx_count=1,
                )

        return G
