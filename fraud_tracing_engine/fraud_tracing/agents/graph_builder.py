import networkx as nx
import pandas as pd

class GraphConstructionAgent:
    def __init__(self):
        pass

    def build_graph(self, transactions_df: pd.DataFrame) -> nx.DiGraph:
        """
        Converts pandas dataframe to directed graph.
        Nodes: Accounts
        Edges: Transactions
        Weights: Amount
        """
        G = nx.DiGraph()
        
        for _, row in transactions_df.iterrows():
            sender = row['sender']
            receiver = row['receiver']
            amount = row['amount']
            timestamp = row['timestamp']
            
            # If the edge exists, we can accumulate amount or keep it as Multigraph. 
            # For simplicity, we accumulate amount if there are multiple transactions.
            if G.has_edge(sender, receiver):
                G[sender][receiver]['amount'] += amount
                # could keeping track of multiple timestamps, but simplifying here
            else:
                G.add_edge(sender, receiver, amount=amount, timestamp=timestamp)
                
        return G
