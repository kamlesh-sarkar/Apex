import json
from typing import Dict, Any, List

class OutputFormatterAgent:
    def __init__(self):
        pass

    def format_output(self, fraud_node: str, kingpin: str, ancestors: List[str], suspicious_edges: List[tuple]) -> str:
        """
        Formats the results into a JSON string suitable for a frontend visualization layer.
        """
        formatted_edges = [
            {"source": u, "target": v, "amount": d.get("amount", 0), "timestamp": str(d.get("timestamp", ""))} 
            for u, v, d in suspicious_edges
        ]
        
        output_dict = {
            "fraud_node": fraud_node,
            "kingpin": kingpin,
            "ancestors": ancestors,
            "suspicious_edges": formatted_edges
        }
        return json.dumps(output_dict, indent=2)
