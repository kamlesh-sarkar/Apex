from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Tuple, Set, Optional
import networkx as nx
import random
import pandas as pd
import os
import tempfile
from pyvis.network import Network
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="GraphSentinel Backend API")

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if not os.path.exists(frontend_path):
    os.makedirs(frontend_path)
app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")

@app.get("/")
def root():
    return RedirectResponse(url="/frontend/index.html")

# Global state for demo purposes (syncing graph with simulation)
GLOBAL_STATE = {
    "transactions": [],
    "fraud_nodes": set(),
    "fraud_edges": set(),
    "kingpin": None,
    "trace_nodes": set(),
    "trace_paths": {}
}

# Allow Streamlit frontend (different port) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Transaction(BaseModel):
    source: str
    target: str
    amount: float

ACCOUNTS = [f"ACC_{i:03d}" for i in range(1, 21)]

def build_nx_graph(df: pd.DataFrame) -> nx.DiGraph:
    G = nx.DiGraph()
    for _, row in df.iterrows():
        if G.has_edge(row["source"], row["target"]):
            G[row["source"]][row["target"]]["weight"] += row["amount"]
            G[row["source"]][row["target"]]["count"] += 1
        else:
            G.add_edge(row["source"], row["target"], weight=row["amount"], count=1)
    return G

def detect_fraud(G: nx.DiGraph) -> Tuple[Set[str], Set[Tuple[str, str]]]:
    fraud_nodes = set()
    fraud_edges = set()
    try:
        cycles = []
        for c in nx.simple_cycles(G):
            cycles.append(c)
            if len(cycles) >= 100:
                break 
        for cycle in cycles:
            if len(cycle) >= 3:
                for node in cycle: fraud_nodes.add(node)
                for i in range(len(cycle)): fraud_edges.add((cycle[i], cycle[(i+1) % len(cycle)]))
    except Exception: pass
    
    # REDUCED SENSITIVITY: increased out-degree threshold from 4 to 6
    for node in G.nodes():
        if G.out_degree(node) >= 6: fraud_nodes.add(node)
        
    # REDUCED SENSITIVITY: increased transaction limit from 4000 to 6000
    for u, v, data in G.edges(data=True):
        if data["weight"] > 6000:
            fraud_nodes.add(u)
            fraud_nodes.add(v)
            fraud_edges.add((u, v))
            
    return fraud_nodes, fraud_edges

def find_kingpin(G: nx.DiGraph, fraud_nodes: Set[str]) -> Optional[str]:
    if not fraud_nodes: return None
    centrality = nx.out_degree_centrality(G)
    fraud_centrality = {n: centrality[n] for n in fraud_nodes if n in centrality}
    if not fraud_centrality: return None
    return max(fraud_centrality, key=fraud_centrality.get)

def traceback(G: nx.DiGraph, kingpin: str) -> Tuple[Set[str], Dict[str, List[str]]]:
    if kingpin is None: return set(), {}
    ancestors = nx.ancestors(G, kingpin)
    paths = {}
    for anc in ancestors:
        try: paths[anc] = nx.shortest_path(G, anc, kingpin)
        except Exception: pass
    return ancestors, paths

@app.get("/api/simulate")
def simulate_transactions(n: int = 40):
    txns = []
    for _ in range(n):
        src = random.choice(ACCOUNTS)
        dst = random.choice([a for a in ACCOUNTS if a != src])
        amount = round(random.uniform(100, 9000), 2)
        txns.append({"source": src, "target": dst, "amount": amount})
    
    # Explicitly add some fraud-likely patterns but within limits
    ring_txns = [
        {"source": "ACC_007", "target": "ACC_013", "amount": 6500.00}, # Should trigger new 6000 limit
        {"source": "ACC_013", "target": "ACC_017", "amount": 6500.00},
        {"source": "ACC_017", "target": "ACC_007", "amount": 6500.00},
    ]
    txns.extend(ring_txns)
    GLOBAL_STATE["transactions"] = txns
    GLOBAL_STATE["fraud_nodes"] = set()
    GLOBAL_STATE["fraud_edges"] = set()
    GLOBAL_STATE["kingpin"] = None
    return {"transactions": txns}

@app.post("/api/analyze")
def analyze_transactions(transactions: List[Transaction]):
    if not transactions: return {}
    df = pd.DataFrame([t.model_dump() for t in transactions])
    G = build_nx_graph(df)
    fn, fe = detect_fraud(G)
    kp = find_kingpin(G, fn)
    tn, tp = traceback(G, kp)
    
    GLOBAL_STATE["fraud_nodes"] = fn
    GLOBAL_STATE["fraud_edges"] = fe
    GLOBAL_STATE["kingpin"] = kp
    GLOBAL_STATE["trace_nodes"] = tn
    GLOBAL_STATE["trace_paths"] = tp
    
    return {
        "fraud_nodes": list(fn),
        "fraud_edges": [{"source": u, "target": v} for u, v in fe],
        "kingpin": kp,
        "trace_nodes": list(tn),
        "trace_paths": tp
    }

@app.get("/api/graph_html")
def get_graph_html(state: str = "simulated"):
    txns = GLOBAL_STATE["transactions"]
    if not txns: return HTMLResponse("<div>No data. Simulate first.</div>")
    
    df = pd.DataFrame(txns)
    G = build_nx_graph(df)
    
    fraud_nodes = GLOBAL_STATE["fraud_nodes"] if state in ["fraud", "traced"] else set()
    fraud_edges = GLOBAL_STATE["fraud_edges"] if state in ["fraud", "traced"] else set()
    kingpin = GLOBAL_STATE["kingpin"] if state in ["fraud", "traced"] else None
    trace_nodes = GLOBAL_STATE.get("trace_nodes", set()) if state == "traced" else set()
    trace_paths = GLOBAL_STATE.get("trace_paths", {}) if state == "traced" else {}

    net = Network(height="100%", width="100%", directed=True, bgcolor="#0e0e0e", font_color="#777575")
    net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=150, spring_strength=0.05)

    trace_edge_set = set()
    for path in trace_paths.values():
        for i in range(len(path) - 1):
            trace_edge_set.add((path[i], path[i+1]))

    for node in G.nodes():
        if node == kingpin:
            color, size = "#77bb04", 35
        elif node in fraud_nodes:
            color, size = "#ff7351", 25
        elif node in trace_nodes:
            color, size = "#8bfcb5", 20
        else:
            color, size = "#262626", 15
            
        net.add_node(node, label=node, size=size, color=color, 
                     font={'color': 'white', 'size': 12},
                     borderWidth=2, borderColor="#ffffff33")

    for u, v, data in G.edges(data=True):
        is_fraud = (u,v) in fraud_edges
        is_trace = (u,v) in trace_edge_set
        
        if is_fraud: color, width = "#ff7351", 3
        elif is_trace: color, width = "#8bfcb5", 2
        else: color, width = "#ffffff22", 1
            
        net.add_edge(u, v, color=color, width=width)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
        path = f.name
    net.save_graph(path)
    with open(path, "r", encoding="utf-8") as f:
        html_content = f.read()
    os.unlink(path)
    
    # Inject style to match code.html
    custom_style = """
    <style>
    body { background-color: #0e0e0e !important; }
    .vis-network { outline: none !important; }
    </style>
    """
    html_content = html_content.replace("</head>", custom_style + "</head>")
    
    return HTMLResponse(content=html_content)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)

