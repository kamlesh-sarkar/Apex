import networkx as nx
import json
from mock_data import incoming_transactions

class ApexGraphEngine:
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def ingest_data(self, transactions):
        for txn in transactions:
            self.graph.add_node(txn["src"], type="user")
            self.graph.add_node(txn["dst"], type="user")
            self.graph.add_node(txn["device_id"], type="device")
            
            self.graph.add_edge(txn["src"], txn["dst"], key=txn["txn_id"], amount=txn["amount"], relation="TRANSFERRED_TO")
            self.graph.add_edge(txn["src"], txn["device_id"], relation="USED_DEVICE")

    def detect_shared_devices(self):
        print("\n--- Running Shared Device Scan ---")
        suspicious_users = set()
        device_nodes = [n for n, attr in self.graph.nodes(data=True) if attr.get("type") == "device"]

        for device in device_nodes:
            connected_users = list(self.graph.predecessors(device))
            if len(set(connected_users)) > 1:
                print(f"🚨 ALERT: Device {device} shared by: {connected_users}")
                suspicious_users.update(connected_users)
        return list(suspicious_users)

    def detect_velocity(self, threshold=2):
        print("\n--- Running Velocity Scan ---")
        suspicious_users = []
        user_nodes = [n for n, attr in self.graph.nodes(data=True) if attr.get("type") == "user"]

        for user in user_nodes:
            out_edges = [e for e in self.graph.out_edges(user, data=True) if e[2].get('relation') == 'TRANSFERRED_TO']
            if len(out_edges) >= threshold:
                print(f"🚨 ALERT: User {user} triggered velocity rules.")
                suspicious_users.append(user)
        return suspicious_users

    def detect_smurfing_loops(self):
        """Rule 3: Catch circular money flows (A -> B -> C -> A)"""
        print("\n--- Running Smurfing Loop Scan ---")
        suspicious_users = set()
        
        # NetworkX has a built-in algorithm to find directed cycles!
        # Because device edges only go one way (User -> Device), they won't trigger false loops.
        # Safety cap: dense graphs can produce thousands of cycles, hanging forever
        cycles = []
        for c in nx.simple_cycles(self.graph):
            cycles.append(c)
            if len(cycles) >= 100:
                break
        
        for cycle in cycles:
            # A cycle of 2 (A->B, B->A) might just be a split bill. A cycle of 3+ is highly suspicious.
            if len(cycle) >= 3:
                print(f"🚨 ALERT: Money laundering loop detected: {' -> '.join(cycle)} -> {cycle[0]}")
                suspicious_users.update(cycle)
                
        return list(suspicious_users)

    def generate_risk_report(self):
        """Compile all rules into a final JSON risk report."""
        print("\n--- Compiling Final Risk Scores ---")
        
        bad_devices = self.detect_shared_devices()
        fast_spenders = self.detect_velocity(threshold=2)
        smurfers = self.detect_smurfing_loops()
        
        report = {"fraud_nodes": []}
        user_nodes = [n for n, attr in self.graph.nodes(data=True) if attr.get("type") == "user"]
        
        for user in user_nodes:
            score = 0
            reasons = []
            
            if user in bad_devices:
                score += 50
                reasons.append("Synthetic Identity (Shared Device)")
            if user in smurfers:
                score += 45
                reasons.append("Smurfing Ring (Circular Flow)")
            if user in fast_spenders:
                score += 30
                reasons.append("High Transaction Velocity")
                
            # Only add to report if they scored points
            if score > 0:
                report["fraud_nodes"].append({
                    "user_id": user,
                    "risk_score": min(score, 100), # Cap at 100
                    "flags": reasons
                })
                
        return report

# --- Execution Block ---
if __name__ == "__main__":
    apex = ApexGraphEngine()
    print("Ingesting transaction stream into Apex...")
    apex.ingest_data(incoming_transactions)
    
    # Generate the final output
    final_report = apex.generate_risk_report()
    
    print("\n✅ FINAL APEX OUTPUT (Ready for API):")
    print(json.dumps(final_report, indent=2))