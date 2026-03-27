"""
🔍 Fraud Detection Dashboard
Frontend: Streamlit + PyVis + Plotly
Run: streamlit run fraud_dashboard.py
Install: pip install streamlit pyvis plotly networkx pandas
"""

import streamlit as st
import networkx as nx
from pyvis.network import Network
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import random
import tempfile
import os

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="FraudLens",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS — dark cyber aesthetic
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Space+Grotesk:wght@300;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: #0a0e1a;
    color: #e0e6f0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0d1120;
    border-right: 1px solid #1e2a45;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #111827;
    border: 1px solid #1e2a45;
    border-radius: 10px;
    padding: 16px;
}
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem !important;
    color: #38bdf8 !important;
}
[data-testid="stMetricLabel"] { color: #64748b !important; }

/* Buttons */
.stButton > button {
    background: transparent;
    color: #38bdf8;
    border: 1.5px solid #38bdf8;
    border-radius: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    letter-spacing: 0.05em;
    padding: 10px 20px;
    transition: all 0.2s ease;
    width: 100%;
}
.stButton > button:hover {
    background: #38bdf8;
    color: #0a0e1a;
    box-shadow: 0 0 18px rgba(56,189,248,0.4);
}

/* Title */
h1 { font-family: 'IBM Plex Mono', monospace; color: #f1f5f9; }
h2, h3 { color: #94a3b8; font-weight: 500; }

/* Divider accent */
hr { border-color: #1e2a45; }

/* Alert boxes */
.stAlert { border-radius: 8px; font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; }

/* DataFrame */
[data-testid="stDataFrame"] { border: 1px solid #1e2a45; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MOCK DATA ENGINE
# ─────────────────────────────────────────────
ACCOUNTS = [f"ACC_{i:03d}" for i in range(1, 21)]
FRAUD_RING = ["ACC_007", "ACC_013", "ACC_017", "ACC_003"]   # hidden fraud cluster

def generate_transactions(n=40):
    txns = []
    for _ in range(n):
        src = random.choice(ACCOUNTS)
        dst = random.choice([a for a in ACCOUNTS if a != src])
        amount = round(random.uniform(100, 9000), 2)
        txns.append({"source": src, "target": dst, "amount": amount})
    # Inject fraud ring transactions
    ring_txns = [
        {"source": "ACC_007", "target": "ACC_013", "amount": 4999.99},
        {"source": "ACC_013", "target": "ACC_017", "amount": 4850.00},
        {"source": "ACC_017", "target": "ACC_003", "amount": 4700.00},
        {"source": "ACC_003", "target": "ACC_007", "amount": 4600.00},
        {"source": "ACC_007", "target": "ACC_017", "amount": 3900.00},
    ]
    txns.extend(ring_txns)
    return pd.DataFrame(txns)


def build_graph(df):
    G = nx.DiGraph()
    for _, row in df.iterrows():
        if G.has_edge(row["source"], row["target"]):
            G[row["source"]][row["target"]]["weight"] += row["amount"]
            G[row["source"]][row["target"]]["count"] += 1
        else:
            G.add_edge(row["source"], row["target"],
                       weight=row["amount"], count=1)
    return G


def detect_fraud(G):
    fraud_nodes = set()
    fraud_edges = set()

    # Rule 1: Cycle detection — nodes part of cycles
    try:
        cycles = list(nx.simple_cycles(G))
        for cycle in cycles:
            if len(cycle) >= 3:
                for node in cycle:
                    fraud_nodes.add(node)
                for i in range(len(cycle)):
                    fraud_edges.add((cycle[i], cycle[(i+1) % len(cycle)]))
    except Exception:
        pass

    # Rule 2: High out-degree (fan-out accounts)
    for node in G.nodes():
        if G.out_degree(node) >= 4:
            fraud_nodes.add(node)

    # Rule 3: Heavy edge weight
    for u, v, data in G.edges(data=True):
        if data["weight"] > 4000:
            fraud_nodes.add(u)
            fraud_nodes.add(v)
            fraud_edges.add((u, v))

    return fraud_nodes, fraud_edges


def find_kingpin(G, fraud_nodes):
    """Highest betweenness centrality among fraud nodes."""
    if not fraud_nodes:
        return None
    centrality = nx.betweenness_centrality(G)
    fraud_centrality = {n: centrality[n] for n in fraud_nodes if n in centrality}
    if not fraud_centrality:
        return None
    return max(fraud_centrality, key=fraud_centrality.get)


def traceback(G, kingpin):
    """All ancestors of the kingpin node."""
    if kingpin is None:
        return set(), {}
    ancestors = nx.ancestors(G, kingpin)
    paths = {}
    for anc in ancestors:
        try:
            path = nx.shortest_path(G, anc, kingpin)
            paths[anc] = path
        except Exception:
            pass
    return ancestors, paths


# ─────────────────────────────────────────────
# PYVIS GRAPH BUILDER
# ─────────────────────────────────────────────
def build_pyvis(G, fraud_nodes=None, fraud_edges=None,
                kingpin=None, trace_nodes=None, trace_paths=None):
    fraud_nodes  = fraud_nodes  or set()
    fraud_edges  = fraud_edges  or set()
    trace_nodes  = trace_nodes  or set()
    trace_paths  = trace_paths  or {}

    net = Network(
        height="560px", width="100%",
        directed=True, bgcolor="#0a0e1a", font_color="#94a3b8"
    )
    net.barnes_hut(gravity=-8000, central_gravity=0.3,
                   spring_length=150, spring_strength=0.05)

    for node in G.nodes():
        if node == kingpin:
            color, size, label = "#f97316", 38, f"👑 {node}"
            border = "#fbbf24"
        elif node in fraud_nodes:
            color, size, label = "#ef4444", 28, f"⚠ {node}"
            border = "#f87171"
        elif node in trace_nodes:
            color, size, label = "#a855f7", 22, node
            border = "#c084fc"
        else:
            color, size, label = "#1e3a5f", 18, node
            border = "#38bdf8"

        net.add_node(
            node, label=label, size=size,
            color={"background": color, "border": border,
                   "highlight": {"background": border, "border": "#fff"}},
            font={"size": 12, "color": "#e2e8f0"},
            title=f"Node: {node}<br>Out-degree: {G.out_degree(node)}<br>In-degree: {G.in_degree(node)}"
        )

    for u, v, data in G.edges(data=True):
        is_fraud_edge  = (u, v) in fraud_edges
        is_trace_edge  = any(
            i < len(p)-1 and p[i] == u and p[i+1] == v
            for p in trace_paths.values()
            for i in range(len(p)-1)
        )
        if is_fraud_edge:
            color, width, dashes = "#ef4444", 3, False
        elif is_trace_edge:
            color, width, dashes = "#a855f7", 2, True
        else:
            color, width, dashes = "#1e3a5f", 1, False

        net.add_edge(
            u, v,
            color=color, width=width, dashes=dashes,
            title=f"${data['weight']:,.2f} | {data['count']} txn(s)"
        )

    # Write to temp file and return HTML string
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
        path = f.name
    net.save_graph(path)
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    os.unlink(path)
    return html


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = None
if "G" not in st.session_state:
    st.session_state.G = None
if "fraud_nodes" not in st.session_state:
    st.session_state.fraud_nodes = set()
if "fraud_edges" not in st.session_state:
    st.session_state.fraud_edges = set()
if "kingpin" not in st.session_state:
    st.session_state.kingpin = None
if "trace_nodes" not in st.session_state:
    st.session_state.trace_nodes = set()
if "trace_paths" not in st.session_state:
    st.session_state.trace_paths = {}
if "mode" not in st.session_state:
    st.session_state.mode = "idle"   # idle | simulated | fraud | traced


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 FraudLens")
    st.markdown("---")

    # ── SIMULATE ──
    if st.button("⚡ Simulate Transactions"):
        st.session_state.df = generate_transactions(40)
        st.session_state.G  = build_graph(st.session_state.df)
        st.session_state.fraud_nodes = set()
        st.session_state.fraud_edges = set()
        st.session_state.kingpin = None
        st.session_state.trace_nodes = set()
        st.session_state.trace_paths = {}
        st.session_state.mode = "simulated"
        st.success("Transactions simulated!")

    st.markdown(" ")

    # ── DETECT FRAUD ──
    if st.button("🚨 Detect Fraud"):
        if st.session_state.G is None:
            st.warning("Simulate transactions first.")
        else:
            fn, fe = detect_fraud(st.session_state.G)
            kp     = find_kingpin(st.session_state.G, fn)
            st.session_state.fraud_nodes = fn
            st.session_state.fraud_edges = fe
            st.session_state.kingpin     = kp
            st.session_state.trace_nodes = set()
            st.session_state.trace_paths = {}
            st.session_state.mode = "fraud"
            st.error(f"{len(fn)} fraud nodes detected!")

    st.markdown(" ")

    # ── TRACE SOURCE ──
    if st.button("🔗 Trace Source"):
        if st.session_state.kingpin is None:
            st.warning("Run Detect Fraud first.")
        else:
            tn, tp = traceback(st.session_state.G, st.session_state.kingpin)
            st.session_state.trace_nodes = tn
            st.session_state.trace_paths = tp
            st.session_state.mode = "traced"
            st.info(f"Traced {len(tn)} ancestor nodes.")

    st.markdown("---")

    # Legend
    st.markdown("**Legend**")
    st.markdown("🟠 `Kingpin` &nbsp; 🔴 `Fraud Node` &nbsp; 🟣 `Trace Path` &nbsp; 🔵 `Clean Node`")

    if st.session_state.kingpin:
        st.markdown("---")
        st.markdown(f"**👑 Kingpin:** `{st.session_state.kingpin}`")


# ─────────────────────────────────────────────
# MAIN PANEL
# ─────────────────────────────────────────────
st.markdown("# 🔍 FraudLens — Transaction Graph")

if st.session_state.mode == "idle":
    st.info("👈 Hit **Simulate Transactions** in the sidebar to get started.")
    st.stop()

df = st.session_state.df
G  = st.session_state.G

# ── METRICS ROW ──────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Transactions", len(df))
col2.metric("Unique Accounts",    G.number_of_nodes())
col3.metric("Fraud Nodes",        len(st.session_state.fraud_nodes))
col4.metric("Kingpin",            st.session_state.kingpin or "—")

st.markdown("---")

# ── GRAPH ────────────────────────────────────
graph_col, info_col = st.columns([3, 1])

with graph_col:
    st.markdown("### 🕸 Transaction Graph")
    html = build_pyvis(
        G,
        fraud_nodes  = st.session_state.fraud_nodes,
        fraud_edges  = st.session_state.fraud_edges,
        kingpin      = st.session_state.kingpin,
        trace_nodes  = st.session_state.trace_nodes,
        trace_paths  = st.session_state.trace_paths,
    )
    st.components.v1.html(html, height=580, scrolling=False)

with info_col:
    st.markdown("### 📋 Fraud Nodes")
    if st.session_state.fraud_nodes:
        for fn in sorted(st.session_state.fraud_nodes):
            icon = "👑" if fn == st.session_state.kingpin else "⚠️"
            st.markdown(f"`{icon} {fn}`")
    else:
        st.caption("No fraud detected yet.")

    if st.session_state.trace_paths:
        st.markdown("### 🔗 Trace Paths")
        for anc, path in list(st.session_state.trace_paths.items())[:6]:
            st.markdown(f"`{'→'.join(path)}`")
        if len(st.session_state.trace_paths) > 6:
            st.caption(f"...+{len(st.session_state.trace_paths)-6} more")

st.markdown("---")

# ── PLOTLY CHARTS ────────────────────────────
chart_a, chart_b = st.columns(2)

with chart_a:
    st.markdown("### 💸 Top 10 Transactions by Amount")
    top_txns = df.nlargest(10, "amount").copy()
    top_txns["label"] = top_txns["source"] + " → " + top_txns["target"]
    top_txns["color"] = top_txns.apply(
        lambda r: "#ef4444" if (r["source"] in st.session_state.fraud_nodes
                                or r["target"] in st.session_state.fraud_nodes)
                  else "#38bdf8", axis=1
    )
    fig1 = go.Figure(go.Bar(
        x=top_txns["amount"], y=top_txns["label"],
        orientation="h",
        marker_color=top_txns["color"],
        text=[f"${a:,.0f}" for a in top_txns["amount"]],
        textposition="inside", textfont=dict(color="white", size=11)
    ))
    fig1.update_layout(
        plot_bgcolor="#0d1120", paper_bgcolor="#0d1120",
        font=dict(color="#94a3b8", family="IBM Plex Mono"),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
        height=340,
    )
    st.plotly_chart(fig1, use_container_width=True)

with chart_b:
    st.markdown("### 📊 Node Degree Distribution")
    degrees = dict(G.out_degree())
    deg_df  = pd.DataFrame({"node": list(degrees.keys()),
                             "degree": list(degrees.values())})
    deg_df["is_fraud"] = deg_df["node"].apply(
        lambda n: "Fraud" if n in st.session_state.fraud_nodes else "Clean"
    )
    fig2 = px.scatter(
        deg_df, x="node", y="degree", color="is_fraud",
        color_discrete_map={"Fraud": "#ef4444", "Clean": "#38bdf8"},
        size="degree", size_max=20,
        labels={"degree": "Out-Degree", "node": "Account"},
    )
    fig2.update_layout(
        plot_bgcolor="#0d1120", paper_bgcolor="#0d1120",
        font=dict(color="#94a3b8", family="IBM Plex Mono"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=340,
        legend=dict(orientation="h", y=1.1, font=dict(size=10)),
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#1e2a45"),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── RAW TABLE ────────────────────────────────
with st.expander("📄 Raw Transaction Log"):
    st.dataframe(df.style.apply(
        lambda row: ["background-color: #3b0d0d" if (row["source"] in st.session_state.fraud_nodes
                     or row["target"] in st.session_state.fraud_nodes) else "" for _ in row],
        axis=1
    ), use_container_width=True)
