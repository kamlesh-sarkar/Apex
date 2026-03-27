"""
🛡️ GraphSentinel — Fraud Detection Command Center
Streamlit + PyVis + Plotly  |  Dark Cybersecurity Theme
Run: streamlit run frontend/fraud_dashboard.py
"""

import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
from pyvis.network import Network
import plotly.graph_objects as go
import pandas as pd
import requests
import tempfile
import os
import time

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="GraphSentinel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# MASSIVE CUSTOM CSS — Cybersecurity Command Center
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── FONTS ──────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── ROOT VARIABLES ────────────────────────────── */
:root {
    --bg-deep:     #060b18;
    --bg-primary:  #0a1128;
    --bg-card:     rgba(13, 20, 42, 0.75);
    --bg-sidebar:  #080e20;
    --cyan:        #00e5ff;
    --blue:        #38bdf8;
    --purple:      #a855f7;
    --red:         #ff3d5a;
    --gold:        #fbbf24;
    --green:       #22c55e;
    --text-primary:   #e2e8f0;
    --text-secondary: #64748b;
    --text-muted:     #475569;
    --border:      rgba(56, 189, 248, 0.08);
    --font-mono:   'JetBrains Mono', monospace;
    --font-body:   'Inter', sans-serif;
}

/* ── GLOBAL OVERRIDES ──────────────────────────── */
html, body, [class*="css"] {
    font-family: var(--font-body) !important;
    color: var(--text-primary) !important;
}

/* Main background */
.stApp {
    background: var(--bg-deep) !important;
    background-image:
        linear-gradient(rgba(0,229,255,.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,229,255,.025) 1px, transparent 1px) !important;
    background-size: 40px 40px !important;
    animation: gridShift 25s linear infinite;
}
@keyframes gridShift {
    0%   { background-position: 0 0; }
    100% { background-position: 40px 40px; }
}

/* Radial glow */
.stApp::before {
    content: '';
    position: fixed;
    top: 30%; left: 50%;
    width: 900px; height: 600px;
    transform: translate(-50%, -50%);
    background: radial-gradient(ellipse, rgba(0,229,255,0.03) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

/* ── HEADER / TOP BAR ──────────────────────────── */
header[data-testid="stHeader"] {
    background: rgba(6, 11, 24, 0.9) !important;
    backdrop-filter: blur(16px) saturate(1.4) !important;
    border-bottom: 1px solid var(--border) !important;
}

/* ── SIDEBAR ───────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdown"] {
    color: var(--text-primary) !important;
}

/* ── METRIC CARDS — Glassmorphism ──────────────── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    backdrop-filter: blur(12px);
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}
[data-testid="stMetric"]:hover {
    border-color: rgba(0, 229, 255, 0.2) !important;
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.08) !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--font-mono) !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: var(--cyan) !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: var(--text-secondary) !important;
}
[data-testid="stMetricDelta"] {
    font-family: var(--font-mono) !important;
}

/* ── BUTTONS — Cyber Neon ──────────────────────── */
.stButton > button {
    background: transparent !important;
    border: 1.5px solid var(--cyan) !important;
    color: var(--cyan) !important;
    border-radius: 8px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    padding: 12px 24px !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
}
.stButton > button:hover {
    background: var(--cyan) !important;
    color: var(--bg-deep) !important;
    box-shadow: 0 0 24px rgba(0, 229, 255, 0.35) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* Red variant buttons (detect) */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) .stButton > button {
    border-color: var(--red) !important;
    color: var(--red) !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) .stButton > button:hover {
    background: var(--red) !important;
    color: #fff !important;
    box-shadow: 0 0 24px rgba(255, 61, 90, 0.35) !important;
}

/* Purple variant buttons (trace) */
div[data-testid="stHorizontalBlock"] > div:nth-child(3) .stButton > button {
    border-color: var(--purple) !important;
    color: var(--purple) !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(3) .stButton > button:hover {
    background: var(--purple) !important;
    color: #fff !important;
    box-shadow: 0 0 24px rgba(168, 85, 247, 0.35) !important;
}

/* ── TYPOGRAPHY ────────────────────────────────── */
h1 {
    font-family: var(--font-mono) !important;
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}
h2, h3 {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
}

/* ── DIVIDERS ──────────────────────────────────── */
hr {
    border-color: var(--border) !important;
}

/* ── ALERTS ────────────────────────────────────── */
.stAlert {
    border-radius: 10px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.8rem !important;
    backdrop-filter: blur(8px) !important;
}
/* Error/fraud alerts */
[data-testid="stAlert"][data-baseweb*="notification"] {
    border-left: 3px solid !important;
}

/* ── EXPANDER ──────────────────────────────────── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(12px) !important;
}
[data-testid="stExpander"] summary {
    font-family: var(--font-mono) !important;
    font-size: 0.85rem !important;
}

/* ── DATAFRAME ─────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ── TABS ──────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.8rem !important;
    padding: 8px 16px !important;
    border: 1px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: var(--cyan) !important;
    background: rgba(0, 229, 255, 0.06) !important;
    border-color: rgba(0, 229, 255, 0.15) !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: var(--cyan) !important;
}

/* ── SCROLLBAR ─────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: rgba(56,189,248,0.15); border-radius: 3px; }

/* ── TOAST ─────────────────────────────────────── */
[data-testid="stToast"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    backdrop-filter: blur(16px) !important;
    font-family: var(--font-mono) !important;
}

/* ── CUSTOM CARD COMPONENT ─────────────────────── */
.cyber-card {
    background: rgba(13, 20, 42, 0.75);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(56, 189, 248, 0.08);
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}
.cyber-card:hover {
    border-color: rgba(0, 229, 255, 0.2);
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.06);
}
.cyber-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.cyber-card.cyan::before    { background: linear-gradient(90deg, #00e5ff, transparent); }
.cyber-card.red::before     { background: linear-gradient(90deg, #ff3d5a, transparent); }
.cyber-card.purple::before  { background: linear-gradient(90deg, #a855f7, transparent); }
.cyber-card.gold::before    { background: linear-gradient(90deg, #fbbf24, transparent); }

.cyber-card-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #64748b;
    margin-bottom: 8px;
}
.cyber-card-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    line-height: 1;
}
.cyber-card-value.cyan   { color: #00e5ff; }
.cyber-card-value.red    { color: #ff3d5a; }
.cyber-card-value.gold   { color: #fbbf24; }
.cyber-card-value.purple { color: #a855f7; }

/* ── ALERT ITEM ────────────────────────────────── */
.alert-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 8px;
    animation: slideIn 0.35s ease-out;
    border-left: 3px solid;
}
.alert-critical {
    background: rgba(255, 61, 90, 0.06);
    border-left-color: #ff3d5a;
}
.alert-warning {
    background: rgba(251, 191, 36, 0.06);
    border-left-color: #fbbf24;
}
.alert-info {
    background: rgba(0, 229, 255, 0.06);
    border-left-color: #00e5ff;
}
.alert-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    font-weight: 600;
    color: #e2e8f0;
}
.alert-desc {
    font-size: 0.72rem;
    color: #64748b;
    margin-top: 2px;
}
@keyframes slideIn {
    from { opacity: 0; transform: translateX(-12px); }
    to   { opacity: 1; transform: translateX(0); }
}

/* ── TRACE PATH CHIPS ──────────────────────────── */
.trace-path {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: rgba(168, 85, 247, 0.06);
    border: 1px solid rgba(168, 85, 247, 0.15);
    border-radius: 6px;
    margin: 4px 2px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #a855f7;
}
.trace-node {
    padding: 2px 6px;
    background: rgba(168, 85, 247, 0.12);
    border-radius: 4px;
}
.trace-node.kingpin {
    background: rgba(251, 191, 36, 0.15);
    color: #fbbf24;
}
.trace-arrow { color: #475569; }

/* ── NODE BADGE ────────────────────────────────── */
.node-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    border-radius: 8px;
    margin: 3px 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    transition: all 0.2s ease;
}
.node-badge:hover {
    transform: translateX(4px);
}
.node-badge.fraud {
    background: rgba(255, 61, 90, 0.08);
    border-left: 3px solid #ff3d5a;
    color: #fca5a5;
}
.node-badge.kingpin {
    background: rgba(251, 191, 36, 0.08);
    border-left: 3px solid #fbbf24;
    color: #fde68a;
}
.node-badge.clean {
    background: rgba(56, 189, 248, 0.06);
    border-left: 3px solid #38bdf8;
    color: #7dd3fc;
}

/* Legend dots */
.legend-row {
    display: flex;
    gap: 18px;
    padding: 10px 0;
    flex-wrap: wrap;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.72rem;
    color: #64748b;
}
.legend-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    display: inline-block;
}

/* Status indicator */
.status-active {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #22c55e;
    padding: 6px 14px;
    background: rgba(34, 197, 94, 0.06);
    border: 1px solid rgba(34, 197, 94, 0.15);
    border-radius: 20px;
}
.status-dot {
    width: 7px; height: 7px;
    background: #22c55e;
    border-radius: 50%;
    animation: pulseDot 2s ease-in-out infinite;
}
@keyframes pulseDot {
    0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.5); }
    50%      { box-shadow: 0 0 0 6px rgba(34,197,94,0); }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# API CONFIG
# ─────────────────────────────────────────────
API_URL = "http://localhost:8000/api"

# ─────────────────────────────────────────────
# GRAPH ENGINE
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# PYVIS GRAPH BUILDER — Enhanced
# ─────────────────────────────────────────────
def build_pyvis(G, fraud_nodes=None, fraud_edges=None,
                kingpin=None, trace_nodes=None, trace_paths=None):
    fraud_nodes  = fraud_nodes  or set()
    fraud_edges  = fraud_edges  or set()
    trace_nodes  = trace_nodes  or set()
    trace_paths  = trace_paths  or {}

    net = Network(
        height="560px", width="100%",
        directed=True, bgcolor="#050a16", font_color="#94a3b8"
    )
    net.barnes_hut(gravity=-7000, central_gravity=0.25,
                   spring_length=160, spring_strength=0.04)

    for node in G.nodes():
        if node == kingpin:
            color, border = "#f97316", "#fbbf24"
            size, label = 40, f"👑 {node}"
            shadow_color = "#f97316"
        elif node in fraud_nodes:
            color, border = "#ff3d5a", "#f87171"
            size, label = 30, f"⚠ {node}"
            shadow_color = "#ff3d5a"
        elif node in trace_nodes:
            color, border = "#a855f7", "#c084fc"
            size, label = 24, node
            shadow_color = "#a855f7"
        else:
            color, border = "#1e3a5f", "#38bdf8"
            size, label = 18, node
            shadow_color = None

        shadow = True if shadow_color else False

        risk = ""
        if node in fraud_nodes:
            risk = f"<br>🚨 <b style='color:#ff3d5a;'>FRAUD FLAGGED</b>"
        if node == kingpin:
            risk += f"<br>👑 <b style='color:#fbbf24;'>KINGPIN</b>"

        net.add_node(
            node, label=label, size=size,
            color={"background": color, "border": border,
                   "highlight": {"background": border, "border": "#fff"},
                   "hover": {"background": border, "border": "#fff"}},
            font={"size": 11, "color": "#e2e8f0", "face": "JetBrains Mono, monospace"},
            borderWidth=3 if node == kingpin else 2 if node in fraud_nodes else 1,
            shadow={"enabled": shadow, "color": shadow_color or "#000",
                    "size": 15, "x": 0, "y": 0} if shadow else False,
            title=f"""<div style="font-family:'JetBrains Mono',monospace;font-size:12px;
                        padding:10px 14px;background:#0d1120;color:#e2e8f0;
                        border:1px solid {border};border-radius:8px;min-width:160px;">
                <b>{node}</b><br>
                Out-degree: {G.out_degree(node)}<br>
                In-degree: {G.in_degree(node)}{risk}
            </div>"""
        )

    # Build trace-edge set
    trace_edge_set = set()
    for path in trace_paths.values():
        for i in range(len(path) - 1):
            trace_edge_set.add((path[i], path[i+1]))

    for u, v, data in G.edges(data=True):
        is_fraud = (u, v) in fraud_edges
        is_trace = (u, v) in trace_edge_set

        if is_fraud:
            color, width, dashes = "#ff3d5a", 3, False
        elif is_trace:
            color, width, dashes = "#a855f7", 2.5, True
        else:
            color, width, dashes = "rgba(56,189,248,0.2)", 1, False

        net.add_edge(
            u, v,
            color=color, width=width, dashes=dashes,
            smooth={"type": "curvedCW", "roundness": 0.15},
            title=f"${data['weight']:,.2f} | {data['count']} txn(s)"
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
        path = f.name
    net.save_graph(path)
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    os.unlink(path)
    return html


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
defaults = {
    "df": None, "G": None,
    "fraud_nodes": set(), "fraud_edges": set(),
    "kingpin": None,
    "trace_nodes": set(), "trace_paths": {},
    "_hidden_trace_nodes": set(), "_hidden_trace_paths": {},
    "mode": "idle",
    "alerts": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def push_alert(level, title, desc):
    st.session_state.alerts.insert(0, {
        "level": level, "title": title, "desc": desc,
        "time": time.strftime("%H:%M:%S")
    })


# ═════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <span style="font-size:1.4rem;">🛡️</span>
        <span style="font-family:'JetBrains Mono',monospace;font-weight:700;
              font-size:1.15rem;color:#00e5ff;letter-spacing:.04em;">GraphSentinel</span>
    </div>
    """, unsafe_allow_html=True)

    # Status indicator
    st.markdown("""
    <div class="status-active">
        <span class="status-dot"></span> System Active
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # ── Navigation ──
    st.markdown("""
    <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.12em;
         color:#475569;font-weight:600;margin-bottom:12px;">NAVIGATION</div>
    """, unsafe_allow_html=True)

    nav_items = [
        ("🎯", "Overview"), ("🕸️", "Graph View"),
        ("📊", "Risk Analysis"), ("🔔", "Alerts"),
    ]
    for icon, label in nav_items:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;padding:8px 12px;
             border-radius:6px;color:#94a3b8;font-size:0.85rem;margin-bottom:2px;
             cursor:default;transition:all 0.2s;">
            <span>{icon}</span> {label}
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Action Buttons ──
    st.markdown("""
    <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.12em;
         color:#475569;font-weight:600;margin-bottom:12px;">ACTIONS</div>
    """, unsafe_allow_html=True)

    # Simulate
    if st.button("⚡ Simulate Transactions", key="sim"):
        try:
            resp = requests.get(f"{API_URL}/simulate?n=40")
            if resp.status_code == 200:
                data = resp.json()["transactions"]
                st.session_state.df = pd.DataFrame(data)
                st.session_state.G  = build_graph(st.session_state.df)
                st.session_state.fraud_nodes = set()
                st.session_state.fraud_edges = set()
                st.session_state.kingpin = None
                st.session_state.trace_nodes = set()
                st.session_state.trace_paths = {}
                st.session_state.mode = "simulated"
                st.session_state.alerts = []
                push_alert("info", "Transactions Simulated",
                           f"{len(data)} transactions loaded into the graph")
                st.rerun()
            else:
                st.error("API returned an error.")
        except Exception as e:
            st.error(f"Cannot reach backend: {e}")

    # Detect Fraud
    if st.button("🚨 Detect Fraud", key="det"):
        if st.session_state.df is None:
            st.warning("Simulate transactions first.")
        else:
            try:
                payload = st.session_state.df.to_dict(orient="records")
                resp = requests.post(f"{API_URL}/analyze", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.fraud_nodes = set(data.get("fraud_nodes", []))
                    st.session_state.fraud_edges = {
                        (e["source"], e["target"]) for e in data.get("fraud_edges", [])
                    }
                    st.session_state.kingpin = data.get("kingpin")
                    st.session_state._hidden_trace_nodes = set(data.get("trace_nodes", []))
                    st.session_state._hidden_trace_paths = data.get("trace_paths", {})
                    st.session_state.trace_nodes = set()
                    st.session_state.trace_paths = {}
                    st.session_state.mode = "fraud"
                    push_alert("critical", "Fraud Detected",
                               f"{len(st.session_state.fraud_nodes)} suspicious nodes identified")
                    if st.session_state.kingpin:
                        push_alert("warning", "Kingpin Identified",
                                   f"Node {st.session_state.kingpin} — highest centrality")
                    st.rerun()
                else:
                    st.error("API error during analysis.")
            except Exception as e:
                st.error(f"Cannot reach backend: {e}")

    # Trace Origin
    if st.button("🔗 Trace Origin 🔍", key="trace"):
        if st.session_state.kingpin is None:
            st.warning("Run Detect Fraud first.")
        else:
            st.session_state.trace_nodes = st.session_state._hidden_trace_nodes
            st.session_state.trace_paths = st.session_state._hidden_trace_paths
            st.session_state.mode = "traced"
            push_alert("info", "Origin Traced",
                       f"{len(st.session_state.trace_nodes)} ancestor nodes traced")
            st.rerun()

    st.markdown("---")

    # Legend
    st.markdown("""
    <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.12em;
         color:#475569;font-weight:600;margin-bottom:10px;">LEGEND</div>
    <div class="legend-row">
        <div class="legend-item"><span class="legend-dot" style="background:#38bdf8;"></span> Normal</div>
        <div class="legend-item"><span class="legend-dot" style="background:#ff3d5a;"></span> Fraud</div>
        <div class="legend-item"><span class="legend-dot" style="background:#fbbf24;"></span> Kingpin</div>
        <div class="legend-item"><span class="legend-dot" style="background:#a855f7;"></span> Trace</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.kingpin:
        st.markdown(f"""
        <div style="margin-top:16px;padding:12px 16px;background:rgba(251,191,36,0.08);
             border:1px solid rgba(251,191,36,0.2);border-radius:8px;
             font-family:'JetBrains Mono',monospace;font-size:0.82rem;color:#fbbf24;">
            👑 Kingpin: <b>{st.session_state.kingpin}</b>
        </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════
# MAIN PANEL
# ═════════════════════════════════════════════

# ── Top Bar ──
top_left, top_right = st.columns([3, 1])
with top_left:
    st.markdown("# 🛡️ GraphSentinel")
with top_right:
    st.markdown("""
    <div style="display:flex;justify-content:flex-end;align-items:center;gap:16px;padding-top:12px;">
        <div class="status-active"><span class="status-dot"></span> System Active</div>
    </div>
    """, unsafe_allow_html=True)

# ── Tabs ──
tab_dash, tab_txns, tab_detect, tab_trace = st.tabs([
    "📊 Dashboard", "💰 Transactions", "🔍 Detection", "🗺️ Traceback"
])

# ═════════════════════════════════════════════
# TAB: DASHBOARD
# ═════════════════════════════════════════════
with tab_dash:
    if st.session_state.mode == "idle":
        st.markdown("""
        <div style="text-align:center;padding:80px 20px;color:#475569;">
            <div style="font-size:3rem;margin-bottom:16px;">🛡️</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;
                 color:#64748b;margin-bottom:8px;">GraphSentinel Ready</div>
            <div style="font-size:0.85rem;">Click <b>⚡ Simulate Transactions</b>
                 in the sidebar to begin analysis</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        df = st.session_state.df
        G  = st.session_state.G

        # ── Stats Cards ──
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="cyber-card cyan">
                <div class="cyber-card-title">💠 Total Transactions</div>
                <div class="cyber-card-value cyan">{len(df)}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="cyber-card red">
                <div class="cyber-card-title">🚨 Fraud Detected</div>
                <div class="cyber-card-value red">{len(st.session_state.fraud_nodes)}</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="cyber-card gold">
                <div class="cyber-card-title">🔔 Active Alerts</div>
                <div class="cyber-card-value gold">{len(st.session_state.alerts)}</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            unique = G.number_of_nodes()
            risk_avg = round((len(st.session_state.fraud_nodes) / max(1, unique)) * 100)
            st.markdown(f"""
            <div class="cyber-card purple">
                <div class="cyber-card-title">📈 Risk Score Avg</div>
                <div class="cyber-card-value purple">{risk_avg}%</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("")

        # ── Graph + Flagged Nodes ──
        graph_col, info_col = st.columns([3, 1])

        with graph_col:
            st.markdown("### 🕸️ Transaction Network Graph")
            html = build_pyvis(
                G,
                fraud_nodes  = st.session_state.fraud_nodes,
                fraud_edges  = st.session_state.fraud_edges,
                kingpin      = st.session_state.kingpin,
                trace_nodes  = st.session_state.trace_nodes,
                trace_paths  = st.session_state.trace_paths,
            )
            components.html(html, height=580, scrolling=False)

        with info_col:
            st.markdown("### 🛡️ Flagged Nodes")
            if st.session_state.fraud_nodes:
                if st.session_state.kingpin:
                    st.markdown(f"""<div class="node-badge kingpin">
                        👑 {st.session_state.kingpin}</div>""", unsafe_allow_html=True)
                for fn in sorted(st.session_state.fraud_nodes):
                    if fn != st.session_state.kingpin:
                        st.markdown(f"""<div class="node-badge fraud">
                            ⚠️ {fn}</div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div style="color:#475569;font-size:0.82rem;padding:20px 0;
                     text-align:center;">No fraud detected yet</div>""", unsafe_allow_html=True)

        # ── Alerts Panel ──
        if st.session_state.alerts:
            st.markdown("### 🔔 Real-Time Alerts")
            alerts_html = ""
            for a in st.session_state.alerts[:10]:
                css_class = f"alert-{a['level']}"
                icon = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(a["level"], "ℹ️")
                alerts_html += f"""
                <div class="alert-item {css_class}">
                    <div>
                        <div class="alert-title">{icon} {a['title']}</div>
                        <div class="alert-desc">{a['desc']}</div>
                    </div>
                    <div style="font-size:0.65rem;color:#475569;font-family:'JetBrains Mono',monospace;
                         white-space:nowrap;margin-left:auto;">{a['time']}</div>
                </div>"""
            st.markdown(alerts_html, unsafe_allow_html=True)


# ═════════════════════════════════════════════
# TAB: TRANSACTIONS
# ═════════════════════════════════════════════
with tab_txns:
    if st.session_state.df is not None:
        df = st.session_state.df
        st.markdown("### 💰 Transaction Log")

        # Top 10 bar chart
        st.markdown("#### 💸 Top 10 Transactions by Amount")
        top_txns = df.nlargest(10, "amount").copy()
        top_txns["label"] = top_txns["source"] + " → " + top_txns["target"]
        top_txns["color"] = top_txns.apply(
            lambda r: "#ff3d5a" if (r["source"] in st.session_state.fraud_nodes
                                    or r["target"] in st.session_state.fraud_nodes)
                      else "#00e5ff", axis=1
        )
        fig = go.Figure(go.Bar(
            x=top_txns["amount"], y=top_txns["label"],
            orientation="h",
            marker_color=top_txns["color"],
            text=[f"${a:,.0f}" for a in top_txns["amount"]],
            textposition="inside",
            textfont=dict(color="white", size=11, family="JetBrains Mono")
        ))
        fig.update_layout(
            plot_bgcolor="#0a1128", paper_bgcolor="#0a1128",
            font=dict(color="#94a3b8", family="JetBrains Mono"),
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, tickfont=dict(size=10)),
            height=320,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Full table
        st.markdown("#### 📋 Full Transaction Table")
        st.dataframe(df.style.apply(
            lambda row: ["background-color: rgba(255,61,90,0.08)"
                         if (row["source"] in st.session_state.fraud_nodes
                             or row["target"] in st.session_state.fraud_nodes)
                         else "" for _ in row],
            axis=1
        ), use_container_width=True, height=400)
    else:
        st.info("👈 Simulate transactions to see data here.")


# ═════════════════════════════════════════════
# TAB: DETECTION
# ═════════════════════════════════════════════
with tab_detect:
    if st.session_state.G is not None and st.session_state.fraud_nodes:
        G = st.session_state.G
        st.markdown("### 🔍 Fraud Detection Analysis")

        # Degree distribution
        st.markdown("#### 📊 Node Degree Distribution")
        degrees = dict(G.out_degree())
        deg_df = pd.DataFrame({"node": list(degrees.keys()),
                                "degree": list(degrees.values())})
        deg_df["status"] = deg_df["node"].apply(
            lambda n: "👑 Kingpin" if n == st.session_state.kingpin
                      else "⚠ Fraud" if n in st.session_state.fraud_nodes
                      else "✓ Clean"
        )
        import plotly.express as px
        fig2 = px.scatter(
            deg_df, x="node", y="degree", color="status",
            color_discrete_map={
                "⚠ Fraud": "#ff3d5a", "✓ Clean": "#38bdf8",
                "👑 Kingpin": "#fbbf24"
            },
            size="degree", size_max=22,
            labels={"degree": "Out-Degree", "node": "Account"},
        )
        fig2.update_layout(
            plot_bgcolor="#0a1128", paper_bgcolor="#0a1128",
            font=dict(color="#94a3b8", family="JetBrains Mono"),
            margin=dict(l=10, r=10, t=10, b=10),
            height=360,
            legend=dict(orientation="h", y=1.1, font=dict(size=10)),
            xaxis=dict(showticklabels=False, showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(56,189,248,0.08)"),
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Summary
        st.markdown("#### 📋 Detection Summary")
        det_c1, det_c2, det_c3 = st.columns(3)
        det_c1.metric("Fraud Nodes", len(st.session_state.fraud_nodes))
        det_c2.metric("Fraud Edges", len(st.session_state.fraud_edges))
        det_c3.metric("Kingpin", st.session_state.kingpin or "—")
    else:
        st.info("👈 Run **Simulate → Detect Fraud** to see analysis here.")


# ═════════════════════════════════════════════
# TAB: TRACEBACK
# ═════════════════════════════════════════════
with tab_trace:
    if st.session_state.mode == "traced" and st.session_state.trace_paths:
        st.markdown("### 🗺️ Origin Traceback")

        # Kingpin banner
        st.markdown(f"""
        <div style="padding:14px 20px;background:rgba(251,191,36,0.08);
             border:1px solid rgba(251,191,36,0.2);border-radius:10px;
             font-family:'JetBrains Mono',monospace;font-size:0.9rem;
             color:#fbbf24;display:flex;align-items:center;gap:10px;margin-bottom:20px;">
            <span style="font-size:1.3rem;">👑</span>
            Suspected Origin Detected: <b>{st.session_state.kingpin}</b>
        </div>""", unsafe_allow_html=True)

        st.markdown("#### 🔗 Trace Paths to Kingpin")
        for anc, path in list(st.session_state.trace_paths.items())[:12]:
            path_html = '<div class="trace-path">'
            for i, node in enumerate(path):
                is_kp = node == st.session_state.kingpin
                cls = "trace-node kingpin" if is_kp else "trace-node"
                prefix = "👑 " if is_kp else ""
                path_html += f'<span class="{cls}">{prefix}{node}</span>'
                if i < len(path) - 1:
                    path_html += '<span class="trace-arrow"> → </span>'
            path_html += '</div>'
            st.markdown(path_html, unsafe_allow_html=True)

        if len(st.session_state.trace_paths) > 12:
            st.caption(f"+{len(st.session_state.trace_paths) - 12} more paths")

        # Trace graph (focused view)
        st.markdown("#### 🕸️ Trace Network View")
        html = build_pyvis(
            st.session_state.G,
            fraud_nodes  = st.session_state.fraud_nodes,
            fraud_edges  = st.session_state.fraud_edges,
            kingpin      = st.session_state.kingpin,
            trace_nodes  = st.session_state.trace_nodes,
            trace_paths  = st.session_state.trace_paths,
        )
        components.html(html, height=500, scrolling=False)
    else:
        st.info("👈 Run **Simulate → Detect Fraud → Trace Origin** to see traceback here.")
