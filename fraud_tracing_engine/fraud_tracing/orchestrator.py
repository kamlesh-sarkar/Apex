"""
FraudTracingOrchestrator (Hybrid: Graph + ML)
Coordinates all agents in sequence to produce context-aware,
explainable fraud detection with XGBoost ML scoring.

Pipeline:
  [1]  DataIngestion        →  raw DataFrame
  [2]  GraphConstruction    →  nx.DiGraph
  [3]  BehavioralAnalysis   →  behavioral_flags per node (enhanced features)
  [3.5] MLClassifier        →  XGBoost fraud probabilities per node
  [4]  NetworkContext       →  network_flags per node (cycles, hubs, clusters)
  [5]  RiskScoring          →  hybrid score: rules + ML per node
  [6]  TracebackValidation  →  filtered ancestors + trace paths
  [7]  KingpinDetection     →  kingpin node
  [8]  Explainability       →  human-readable reasons per node
  [9]  ModelEvaluation      →  AUC, confusion matrix, ROC curve
  [10] OutputFormatter      →  final JSON
"""
import json
from .agents.ingestion            import DataIngestionAgent
from .agents.graph_builder        import GraphConstructionAgent
from .agents.behavioral_analysis  import BehavioralAnalysisAgent
from .agents.ml_classifier        import MLClassifierAgent
from .agents.network_context      import NetworkContextAgent
from .agents.risk_scoring         import RiskScoringAgent
from .agents.traceback            import TracebackAgent
from .agents.kingpin              import KingpinDetectionAgent
from .agents.explainability       import ExplainabilityAgent
from .agents.evaluation           import ModelEvaluationAgent
from .agents.formatter            import OutputFormatterAgent


class FraudTracingOrchestrator:
    def __init__(self, project_id=None, use_mock=True):
        self.ingestion_agent    = DataIngestionAgent(project_id=project_id, use_mock=use_mock)
        self.graph_builder      = GraphConstructionAgent()
        self.behavioral_agent   = BehavioralAnalysisAgent()
        self.ml_classifier      = MLClassifierAgent()
        self.network_agent      = NetworkContextAgent()
        self.risk_agent         = RiskScoringAgent()
        self.traceback_agent    = TracebackAgent()
        self.kingpin_agent      = KingpinDetectionAgent()
        self.explain_agent      = ExplainabilityAgent()
        self.evaluation_agent   = ModelEvaluationAgent()
        self.formatter_agent    = OutputFormatterAgent()

        # Train ML model ONCE at startup (not per-request)
        print("[Init] Pre-training XGBoost model...")
        self.ml_metrics = self.ml_classifier.train()
        print(f"[Init] ML model ready. AUC: {self.ml_metrics['auc_roc']}")

    def run_pipeline(self, fraud_node: str, query: str = None) -> str:
        """
        Executes the full hybrid (graph + ML) fraud detection pipeline.

        Returns a JSON string with the schema:
        {
          "node", "risk_score", "risk_score_value", "is_fraud",
          "fraud_probability", "reasons", "kingpin", "trace_paths",
          "suspicious_edges", "all_node_scores",
          "ml_metrics", "evaluation_report"
        }
        """
        # ── Step 1: Ingest Data ────────────────────────────────────────────
        print("[Agent 1] Ingesting transaction data...")
        df = self.ingestion_agent.fetch_transactions(query)
        print(f"  → {len(df)} transactions loaded.")

        # ── Step 2: Build Graph ────────────────────────────────────────────
        print("[Agent 2] Constructing transaction graph...")
        G = self.graph_builder.build_graph(df)
        print(f"  → Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")

        if fraud_node not in G:
            return json.dumps({"error": f"Node '{fraud_node}' not found in graph."})

        # ── Step 3: Behavioral Analysis (Enhanced) ─────────────────────────
        print("[Agent 3] Running enhanced behavioral analysis...")
        behavioral_flags = self.behavioral_agent.analyze(df)
        print(f"  → Behavioral profiles computed for {len(behavioral_flags)} nodes.")

        # ── Step 3.5: XGBoost ML Classification (model pre-trained) ───────
        print("[Agent 3.5] Running ML predictions (pre-trained model)...")
        ml_metrics = self.ml_metrics  # Reuse cached metrics from init
        ml_predictions = self.ml_classifier.predict(df, precomputed_features=behavioral_flags)
        ml_flagged = sum(1 for p in ml_predictions.values() if p["fraud_probability"] > 0.5)
        print(f"  → ML AUC: {ml_metrics['auc_roc']} | {ml_flagged} nodes flagged by ML.")

        # ── Step 4: Network Context Analysis ──────────────────────────────
        print("[Agent 4] Analyzing network structure (graphs preserved)...")
        network_flags = self.network_agent.analyze(G)
        print(f"  → Network flags computed for {len(network_flags)} nodes.")

        # ── Step 5: Hybrid Risk Scoring (Rules + ML) ──────────────────────
        print("[Agent 5] Computing hybrid risk scores (rules + ML)...")
        node_scores = self.risk_agent.score(behavioral_flags, network_flags, ml_predictions)
        high_risk_nodes = [n for n, s in node_scores.items() if s["label"] == "High"]
        print(f"  → High-risk nodes: {high_risk_nodes}")

        # ── Step 6: Traceback Validation ───────────────────────────────────
        print(f"[Agent 6] Tracing origins for node '{fraud_node}' (with risk filtering)...")
        trace_result = self.traceback_agent.trace_origins(G, fraud_node, node_scores=node_scores)

        if "error" in trace_result:
            return json.dumps(trace_result)

        ancestors          = trace_result["ancestors"]
        suspicious_edges   = trace_result["suspicious_edges"]
        suspicious_subgraph = trace_result["suspicious_subgraph"]
        trace_paths        = trace_result["trace_paths"]
        print(f"  → {len(ancestors)} suspicious ancestors | {len(trace_paths)} trace paths found.")

        # ── Step 7: Kingpin Detection ──────────────────────────────────────
        print("[Agent 7] Identifying kingpin...")
        kingpin = self.kingpin_agent.identify_kingpin(suspicious_subgraph, fraud_node)
        print(f"  → Kingpin: {kingpin}")

        # ── Step 8: Explainability ─────────────────────────────────────────
        print("[Agent 8] Generating explainability report...")
        reasons = self.explain_agent.generate_reasons(node_scores)

        # ── Step 9: Model Evaluation ──────────────────────────────────────
        print("[Agent 9] Compiling ML evaluation metrics...")
        evaluation_report = self.evaluation_agent.generate_evaluation_report(
            ml_metrics, node_scores, ml_predictions
        )
        print(f"  → Rule-ML agreement rate: {evaluation_report['scoring_analysis']['rule_ml_agreement_rate']}")

        # ── Step 10: Format Output ─────────────────────────────────────────
        print("[Agent 10] Formatting final output...")
        result_json = self.formatter_agent.format_output(
            fraud_node=fraud_node,
            kingpin=kingpin,
            node_scores=node_scores,
            reasons=reasons,
            suspicious_edges=suspicious_edges,
            trace_paths=trace_paths,
            ml_predictions=ml_predictions,
            ml_metrics=ml_metrics,
            evaluation_report=evaluation_report,
        )

        return result_json

