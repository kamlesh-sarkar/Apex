/* ═══════════════════════════════════════════════════
   GraphSentinel — Frontend Logic
   vis-network graph + API hooks + interactivity
   ═══════════════════════════════════════════════════ */

const API_URL = window.location.origin + '/api';

// ── STATE ───────────────────────────────────────────
const state = {
  transactions: [],
  fraudNodes:   new Set(),
  fraudEdges:   new Set(),
  kingpin:      null,
  traceNodes:   new Set(),
  tracePaths:   {},
  graph:        null,   // vis.Network instance
  network:      null,
  nodesDataset: null,
  edgesDataset: null,
  mode:         'idle'  // idle | simulated | fraud | traced
};

// ── DOM REFS ────────────────────────────────────────
const $ = id => document.getElementById(id);

const els = {
  statTxns:       $('stat-txns'),
  statFraud:      $('stat-fraud'),
  statAlerts:     $('stat-alerts'),
  statRisk:       $('stat-risk'),
  btnSimulate:    $('btn-simulate'),
  btnDetect:      $('btn-detect'),
  btnTrace:       $('btn-trace'),
  graphContainer: $('graph-container'),
  alertsList:     $('alerts-list'),
  tracePanel:     $('trace-panel'),
  traceBanner:    $('trace-banner'),
  traceBannerText:$('trace-banner-text'),
  tracePaths:     $('trace-paths'),
  nodesList:      $('nodes-list'),
  txnBody:        $('txn-body'),
  alertBadge:     $('alert-badge')
};

// ── UTILITY ─────────────────────────────────────────
function timeNow() {
  return new Date().toLocaleTimeString('en-US', { hour12: false });
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// ── ALERTS ──────────────────────────────────────────
let alertCount = 0;

function pushAlert(type, title, desc) {
  alertCount++;
  if (els.alertBadge) {
    els.alertBadge.textContent = alertCount;
    els.alertBadge.style.display = 'inline';
  }

  const iconMap = {
    critical: 'fa-triangle-exclamation',
    warning:  'fa-shield-halved',
    info:     'fa-circle-info'
  };
  const html = `
    <div class="alert-item alert-item--${type}">
      <i class="fa-solid ${iconMap[type]} alert-item__icon"></i>
      <div class="alert-item__content">
        <div class="alert-item__title">${title}</div>
        <div class="alert-item__desc">${desc}</div>
      </div>
      <div class="alert-item__time">${timeNow()}</div>
    </div>`;
  els.alertsList.insertAdjacentHTML('afterbegin', html);
}

// ── STATS UPDATE ────────────────────────────────────
function updateStats() {
  animateValue(els.statTxns,   parseInt(els.statTxns.textContent)   || 0, state.transactions.length, 500);
  animateValue(els.statFraud,  parseInt(els.statFraud.textContent)  || 0, state.fraudNodes.size, 500);
  animateValue(els.statAlerts, parseInt(els.statAlerts.textContent) || 0, alertCount, 500);

  // Risk score average
  const riskAvg = state.fraudNodes.size > 0
    ? Math.round((state.fraudNodes.size / Math.max(1, getUniqueNodes().size)) * 100)
    : 0;
  animateValue(els.statRisk, parseInt(els.statRisk.textContent) || 0, riskAvg, 500);
}

function animateValue(el, start, end, duration) {
  if (start === end) { el.textContent = end; return; }
  const range = end - start;
  const inc = range > 0 ? 1 : -1;
  const steps = Math.abs(range);
  const stepTime = Math.max(Math.floor(duration / steps), 16);
  let current = start;
  const timer = setInterval(() => {
    current += inc;
    el.textContent = current;
    if (current === end) clearInterval(timer);
  }, stepTime);
}

function getUniqueNodes() {
  const nodes = new Set();
  state.transactions.forEach(t => { nodes.add(t.source); nodes.add(t.target); });
  return nodes;
}

// ── GRAPH RENDERING (vis-network) ───────────────────
function buildGraph() {
  // Build adjacency
  const adjMap = {};
  state.transactions.forEach(t => {
    const key = `${t.source}__${t.target}`;
    if (!adjMap[key]) adjMap[key] = { source: t.source, target: t.target, weight: 0, count: 0 };
    adjMap[key].weight += t.amount;
    adjMap[key].count += 1;
  });

  // Compute degree
  const outDeg = {}, inDeg = {};
  Object.values(adjMap).forEach(e => {
    outDeg[e.source] = (outDeg[e.source] || 0) + 1;
    inDeg[e.target]  = (inDeg[e.target]  || 0) + 1;
  });

  // Nodes
  const uniqueNodes = getUniqueNodes();
  const nodesArr = [];
  uniqueNodes.forEach(id => {
    const isFraud   = state.fraudNodes.has(id);
    const isKingpin = id === state.kingpin;
    const isTrace   = state.traceNodes.has(id);

    let color, borderColor, size, fontColor;
    if (isKingpin) {
      color = '#f97316'; borderColor = '#fbbf24'; size = 42; fontColor = '#fbbf24';
    } else if (isFraud) {
      color = '#ff3d5a'; borderColor = '#f87171'; size = 32; fontColor = '#fca5a5';
    } else if (isTrace) {
      color = '#a855f7'; borderColor = '#c084fc'; size = 26; fontColor = '#d8b4fe';
    } else {
      color = '#1e3a5f'; borderColor = '#38bdf8'; size = 20; fontColor = '#94a3b8';
    }

    let labelPrefix = isKingpin ? '👑 ' : isFraud ? '⚠ ' : '';

    nodesArr.push({
      id,
      label: labelPrefix + id,
      size,
      color: {
        background: color,
        border: borderColor,
        highlight: { background: borderColor, border: '#ffffff' },
        hover:     { background: borderColor, border: '#ffffff' }
      },
      font: { color: fontColor, size: 11, face: 'JetBrains Mono, monospace' },
      borderWidth: isKingpin ? 3 : isFraud ? 2 : 1,
      shadow: (isKingpin || isFraud) ? { enabled: true, color: color, size: 12, x: 0, y: 0 } : false,
      title: `<div style="font-family:'JetBrains Mono',monospace;font-size:12px;padding:6px;background:#0d1120;color:#e2e8f0;border:1px solid ${borderColor};border-radius:6px;">
        <b>${id}</b><br>
        Out-degree: ${outDeg[id] || 0}<br>
        In-degree: ${inDeg[id] || 0}<br>
        ${isFraud ? '<span style="color:#ff3d5a;">⚠ FRAUD FLAGGED</span><br>' : ''}
        ${isKingpin ? '<span style="color:#fbbf24;">👑 KINGPIN</span><br>' : ''}
        ${isTrace ? '<span style="color:#a855f7;">🔗 Trace Path</span>' : ''}
      </div>`
    });
  });

  // Build trace-edge set for highlighting
  const traceEdgeSet = new Set();
  if (state.tracePaths) {
    Object.values(state.tracePaths).forEach(path => {
      for (let i = 0; i < path.length - 1; i++) {
        traceEdgeSet.add(`${path[i]}__${path[i+1]}`);
      }
    });
  }

  // Edges
  const edgesArr = [];
  Object.values(adjMap).forEach(e => {
    const key = `${e.source}__${e.target}`;
    const isFraudEdge = state.fraudEdges.has(key);
    const isTraceEdge = traceEdgeSet.has(key);

    let edgeColor, width, dashes;
    if (isFraudEdge) {
      edgeColor = '#ff3d5a'; width = 3; dashes = false;
    } else if (isTraceEdge) {
      edgeColor = '#a855f7'; width = 2.5; dashes = [8, 6];
    } else {
      edgeColor = 'rgba(56,189,248,0.2)'; width = 1; dashes = false;
    }

    edgesArr.push({
      from: e.source,
      to:   e.target,
      color: { color: edgeColor, highlight: edgeColor, hover: edgeColor },
      width,
      dashes,
      arrows: { to: { enabled: true, scaleFactor: 0.6 } },
      smooth: { type: 'curvedCW', roundness: 0.15 },
      title: `$${e.weight.toLocaleString('en-US', { minimumFractionDigits: 2 })} | ${e.count} txn(s)`
    });
  });

  // Create or update network
  state.nodesDataset = new vis.DataSet(nodesArr);
  state.edgesDataset = new vis.DataSet(edgesArr);

  if (state.network) {
    state.network.setData({ nodes: state.nodesDataset, edges: state.edgesDataset });
  } else {
    const options = {
      physics: {
        enabled: true,
        barnesHut: {
          gravitationalConstant: -6000,
          centralGravity: 0.25,
          springLength: 160,
          springConstant: 0.04,
          damping: 0.12
        },
        stabilization: { iterations: 120, fit: true }
      },
      interaction: {
        hover: true,
        tooltipDelay: 120,
        zoomView: true,
        dragView: true,
        navigationButtons: false
      },
      edges: {
        smooth: { type: 'curvedCW', roundness: 0.15 }
      },
      nodes: {
        shape: 'dot'
      }
    };
    state.network = new vis.Network(els.graphContainer, {
      nodes: state.nodesDataset,
      edges: state.edgesDataset
    }, options);
  }
}

// ── UPDATE SIDE PANEL (Nodes list) ──────────────────
function updateNodesPanel() {
  if (!els.nodesList) return;
  const allNodes = [...getUniqueNodes()].sort();

  if (state.fraudNodes.size === 0 && !state.kingpin) {
    els.nodesList.innerHTML = `
      <div class="empty-state">
        <i class="fa-solid fa-shield-halved"></i>
        <div class="empty-state__text">Run fraud detection to see flagged nodes</div>
      </div>`;
    return;
  }

  let html = '';
  // Kingpin first
  if (state.kingpin) {
    html += nodeInfoItem(state.kingpin, 'kingpin', '👑');
  }
  // Fraud nodes
  [...state.fraudNodes].sort().forEach(n => {
    if (n !== state.kingpin) {
      html += nodeInfoItem(n, 'fraud', '⚠');
    }
  });
  els.nodesList.innerHTML = html;
}

function nodeInfoItem(name, type, icon) {
  const outDeg = state.transactions.filter(t => t.source === name).length;
  const inDeg  = state.transactions.filter(t => t.target === name).length;
  return `
    <div class="node-info__item ${type}">
      <div class="icon">${icon}</div>
      <div class="details">
        <div class="name">${name}</div>
        <div class="meta">Out: ${outDeg} · In: ${inDeg}</div>
      </div>
    </div>`;
}

// ── UPDATE TRANSACTION TABLE ────────────────────────
function updateTxnTable() {
  if (!els.txnBody) return;
  let html = '';
  state.transactions.forEach((t, i) => {
    const isFraud = state.fraudNodes.has(t.source) || state.fraudNodes.has(t.target);
    html += `
      <tr class="${isFraud ? 'fraud-row' : ''}">
        <td>${i + 1}</td>
        <td>${t.source}</td>
        <td>${t.target}</td>
        <td class="amount-cell">$${t.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
        <td>${isFraud ? '<span style="color:var(--red);">⚠ Flagged</span>' : '<span style="color:var(--green);">✓ Clean</span>'}</td>
      </tr>`;
  });
  els.txnBody.innerHTML = html;
}

// ── UPDATE TRACE PANEL ──────────────────────────────
function updateTracePanel() {
  if (!els.tracePaths) return;

  if (!state.kingpin || Object.keys(state.tracePaths).length === 0) {
    els.tracePaths.innerHTML = `
      <div class="empty-state">
        <i class="fa-solid fa-route"></i>
        <div class="empty-state__text">Trace origin to see paths to the kingpin</div>
      </div>`;
    els.traceBanner.classList.remove('visible');
    return;
  }

  els.traceBanner.classList.add('visible');
  els.traceBannerText.textContent = `Suspected Origin: ${state.kingpin}`;

  let html = '';
  const paths = Object.values(state.tracePaths).slice(0, 8);
  paths.forEach(path => {
    html += '<div class="trace-path">';
    path.forEach((node, i) => {
      const isKP = node === state.kingpin;
      html += `<span class="node ${isKP ? 'kingpin' : ''}">${isKP ? '👑 ' : ''}${node}</span>`;
      if (i < path.length - 1) html += '<span class="arrow">→</span>';
    });
    html += '</div>';
  });

  if (Object.keys(state.tracePaths).length > 8) {
    html += `<div style="font-size:0.72rem;color:var(--text-muted);padding:4px 12px;">
      +${Object.keys(state.tracePaths).length - 8} more paths
    </div>`;
  }
  els.tracePaths.innerHTML = html;
}

// ═══════════════════════════════════════════════════
// API HOOKS
// ═══════════════════════════════════════════════════

// ── SIMULATE ────────────────────────────────────────
async function simulateTransactions() {
  const btn = els.btnSimulate;
  btn.classList.add('loading');
  btn.disabled = true;

  try {
    const resp = await fetch(`${API_URL}/simulate?n=40`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    // Reset state
    state.transactions = data.transactions;
    state.fraudNodes   = new Set();
    state.fraudEdges   = new Set();
    state.kingpin      = null;
    state.traceNodes   = new Set();
    state.tracePaths   = {};
    state.mode         = 'simulated';
    alertCount = 0;
    if (els.alertBadge) els.alertBadge.style.display = 'none';
    els.alertsList.innerHTML = '';

    buildGraph();
    updateStats();
    updateNodesPanel();
    updateTxnTable();
    updateTracePanel();

    pushAlert('info', 'Transactions Simulated', `${data.transactions.length} transactions loaded into the graph.`);

    // Enable detect button
    els.btnDetect.disabled = false;
    els.btnTrace.disabled  = true;

  } catch (err) {
    pushAlert('critical', 'Simulation Failed', err.message);
  } finally {
    btn.classList.remove('loading');
    btn.disabled = false;
  }
}

// ── DETECT FRAUD ────────────────────────────────────
async function detectFraud() {
  if (state.transactions.length === 0) {
    pushAlert('warning', 'No Data', 'Simulate transactions first.');
    return;
  }

  const btn = els.btnDetect;
  btn.classList.add('loading');
  btn.disabled = true;

  try {
    const resp = await fetch(`${API_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.transactions)
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    state.fraudNodes = new Set(data.fraud_nodes || []);
    state.fraudEdges = new Set((data.fraud_edges || []).map(e => `${e.source}__${e.target}`));
    state.kingpin    = data.kingpin || null;

    // Store trace data but don't reveal yet
    state._hiddenTraceNodes = new Set(data.trace_nodes || []);
    state._hiddenTracePaths = data.trace_paths || {};
    state.traceNodes = new Set();
    state.tracePaths = {};
    state.mode = 'fraud';

    buildGraph();
    updateStats();
    updateNodesPanel();
    updateTxnTable();
    updateTracePanel();

    // Push alerts
    pushAlert('critical', 'Fraud Detected', `${state.fraudNodes.size} suspicious nodes identified in the network.`);
    if (state.kingpin) {
      pushAlert('warning', 'Kingpin Identified', `Node ${state.kingpin} has the highest centrality among fraud nodes.`);
    }
    if (state.fraudEdges.size > 0) {
      pushAlert('critical', 'Suspicious Clusters', `${state.fraudEdges.size} high-risk transaction edges flagged.`);
    }

    // Enable trace button
    els.btnTrace.disabled = false;

  } catch (err) {
    pushAlert('critical', 'Detection Failed', err.message);
  } finally {
    btn.classList.remove('loading');
    btn.disabled = false;
  }
}

// ── TRACE ORIGIN ────────────────────────────────────
async function traceOrigin() {
  if (!state.kingpin) {
    pushAlert('warning', 'No Kingpin', 'Run fraud detection first to identify the kingpin.');
    return;
  }

  const btn = els.btnTrace;
  btn.classList.add('loading');
  btn.disabled = true;

  await sleep(400); // Dramatic pause

  state.traceNodes = state._hiddenTraceNodes || new Set();
  state.tracePaths = state._hiddenTracePaths || {};
  state.mode = 'traced';

  buildGraph();
  updateStats();
  updateNodesPanel();
  updateTracePanel();

  pushAlert('info', 'Origin Traced', `${state.traceNodes.size} ancestor nodes traced back to kingpin ${state.kingpin}.`);

  btn.classList.remove('loading');
  // Keep trace button disabled after tracing
}

// ── EVENT LISTENERS ─────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  els.btnSimulate.addEventListener('click', simulateTransactions);
  els.btnDetect.addEventListener('click',   detectFraud);
  els.btnTrace.addEventListener('click',    traceOrigin);

  // Sidebar nav active state
  document.querySelectorAll('.sidebar__item').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.sidebar__item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
    });
  });

  // Navbar tab active state
  document.querySelectorAll('.navbar__tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.navbar__tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
    });
  });

  // Initial alert
  pushAlert('info', 'System Online', 'GraphSentinel is ready. Simulate transactions to begin analysis.');
});
