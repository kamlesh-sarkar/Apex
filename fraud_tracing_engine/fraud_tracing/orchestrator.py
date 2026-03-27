import json
from .agents.ingestion import DataIngestionAgent
from .agents.graph_builder import GraphConstructionAgent
from .agents.traceback import TracebackAgent
from .agents.kingpin import KingpinDetectionAgent
from .agents.formatter import OutputFormatterAgent

class FraudTracingOrchestrator:
    def __init__(self, project_id=None, use_mock=True):
        self.ingestion_agent = DataIngestionAgent(project_id=project_id, use_mock=use_mock)
        self.graph_builder = GraphConstructionAgent()
        self.traceback_agent = TracebackAgent()
        self.kingpin_agent = KingpinDetectionAgent()
        self.formatter_agent = OutputFormatterAgent()

    def run_pipeline(self, fraud_node: str, query: str = None) -> str:
        """
        Executes the fraud tracing pipeline:
        BigQuery -> Graph -> Traceback -> Kingpin -> JSON Output
        """
        # 1. Ingest Data
        print("Agent 1: Ingesting data...")
        df = self.ingestion_agent.fetch_transactions(query)
        
        # 2. Build Graph
        print("Agent 2: Building graph...")
        G = self.graph_builder.build_graph(df)
        
        # 3. Traceback
        print(f"Agent 3: Tracing origins for node {fraud_node}...")
        trace_result = self.traceback_agent.trace_origins(G, fraud_node)
        
        if "error" in trace_result:
            return json.dumps(trace_result)
            
        ancestors = trace_result["ancestors"]
        suspicious_edges = trace_result["suspicious_edges"]
        suspicious_subgraph = trace_result["suspicious_subgraph"]
        
        # 4. Kingpin Detection
        print("Agent 4: Identifying kingpin...")
        kingpin = self.kingpin_agent.identify_kingpin(suspicious_subgraph, fraud_node)
        
        # 5. Format Output
        print("Agent 5: Formatting output...")
        result_json = self.formatter_agent.format_output(fraud_node, kingpin, ancestors, suspicious_edges)
        
        return result_json
