/**
 * Health Check Scripts for Network Topology Mapper
 *
 * Self-contained functions designed to run via MCP javascript_tool.
 * Each function returns a JSON result object.
 *
 * Usage: Copy-paste individual function bodies into javascript_tool.
 * Do NOT run the entire file at once — pick the check you need.
 */

// ============================================================
// 1. API HEALTH CHECK
// Hits all major API endpoints and verifies status codes + basic shape.
// ============================================================
// javascript_tool:
(async () => {
  const BASE = 'http://localhost:8000';
  const endpoints = [
    { path: '/',                    expect: ['message', 'version'] },
    { path: '/api/health',          expect: ['status'] },
    { path: '/api/topology',        expect: ['devices', 'connections'] },
    { path: '/api/topology/stats',  expect: ['total_devices', 'total_connections', 'type_counts'] },
    { path: '/api/alerts',          expect: ['alerts'] },
    { path: '/api/scans',           expect: ['scans'] },
    { path: '/api/simulate/spof',   expect: ['spofs'] },
    { path: '/api/reports/resilience', expect: ['generated', 'score'] },
  ];

  const results = [];
  for (const ep of endpoints) {
    try {
      const res = await fetch(BASE + ep.path);
      const json = await res.json();
      const missingKeys = ep.expect.filter(k => !(k in json));
      results.push({
        path: ep.path,
        status: res.status,
        ok: res.ok && missingKeys.length === 0,
        missingKeys: missingKeys.length > 0 ? missingKeys : undefined,
      });
    } catch (e) {
      results.push({ path: ep.path, ok: false, error: e.message });
    }
  }

  const passed = results.filter(r => r.ok).length;
  return {
    summary: `${passed}/${results.length} endpoints healthy`,
    passed,
    total: results.length,
    results,
  };
})()


// ============================================================
// 2. DATA SHAPE VALIDATION — Topology
// Verifies /api/topology response matches TypeScript Device/Connection interfaces.
// ============================================================
// javascript_tool:
(async () => {
  const DEVICE_TYPES = ['router','switch','server','workstation','firewall','ap','printer','iot','unknown'];
  const DEVICE_STATUSES = ['online','offline','degraded'];
  const CONN_TYPES = ['ethernet','fiber','wireless','vpn','virtual'];
  const CONN_STATUSES = ['active','disabled','degraded','flapping'];

  const DEVICE_REQUIRED = ['id','ip','mac','hostname','device_type','vendor','model','os',
    'open_ports','services','first_seen','last_seen','discovery_method',
    'vlan_ids','subnet','location','risk_score','criticality','is_gateway','status'];

  const CONN_REQUIRED = ['id','source_id','target_id','connection_type','bandwidth',
    'switch_port','latency_ms','packet_loss_pct','is_redundant','protocol','status',
    'first_seen','last_seen'];

  const res = await fetch('http://localhost:8000/api/topology');
  const data = await res.json();

  const deviceErrors = [];
  const connErrors = [];

  // Validate first 5 devices
  data.devices.slice(0, 5).forEach((d, i) => {
    const missing = DEVICE_REQUIRED.filter(k => !(k in d));
    if (missing.length > 0) deviceErrors.push({ index: i, id: d.id, missing });
    if (!DEVICE_TYPES.includes(d.device_type)) deviceErrors.push({ index: i, id: d.id, badType: d.device_type });
    if (!DEVICE_STATUSES.includes(d.status)) deviceErrors.push({ index: i, id: d.id, badStatus: d.status });
    if (typeof d.risk_score !== 'number') deviceErrors.push({ index: i, id: d.id, riskNotNumber: typeof d.risk_score });
    if (!Array.isArray(d.open_ports)) deviceErrors.push({ index: i, id: d.id, portsNotArray: true });
  });

  // Validate first 5 connections
  data.connections.slice(0, 5).forEach((c, i) => {
    const missing = CONN_REQUIRED.filter(k => !(k in c));
    if (missing.length > 0) connErrors.push({ index: i, id: c.id, missing });
    if (!CONN_TYPES.includes(c.connection_type)) connErrors.push({ index: i, id: c.id, badType: c.connection_type });
    if (!CONN_STATUSES.includes(c.status)) connErrors.push({ index: i, id: c.id, badStatus: c.status });
  });

  return {
    devices: { total: data.devices.length, sampled: Math.min(5, data.devices.length), errors: deviceErrors },
    connections: { total: data.connections.length, sampled: Math.min(5, data.connections.length), errors: connErrors },
    dependencies: { total: (data.dependencies || []).length },
    ok: deviceErrors.length === 0 && connErrors.length === 0,
  };
})()


// ============================================================
// 3. VISUAL INTEGRITY CHECK
// Finds elements with 0 width and 0 height that should be visible.
// ============================================================
// javascript_tool:
(() => {
  const IGNORE_TAGS = ['SCRIPT','STYLE','META','LINK','HEAD','BR','HR','WBR','COL','TEMPLATE','NOSCRIPT'];
  const problems = [];

  document.querySelectorAll('*').forEach(el => {
    if (IGNORE_TAGS.includes(el.tagName)) return;
    const style = getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return;

    const rect = el.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0 && el.children.length > 0) {
      problems.push({
        tag: el.tagName,
        id: el.id || undefined,
        classes: el.className?.toString().slice(0, 80) || undefined,
        text: el.textContent?.slice(0, 40) || undefined,
      });
    }
  });

  return {
    ok: problems.length === 0,
    zeroDimElements: problems.length,
    problems: problems.slice(0, 10),
  };
})()


// ============================================================
// 4. STUCK LOADING STATE DETECTION
// Finds visible "Loading..." text, active spinners, or skeleton screens.
// ============================================================
// javascript_tool:
(() => {
  const loadingIndicators = [];

  // Check for visible text containing "Loading"
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const text = walker.currentNode.textContent.trim();
    if (/loading|spinner|skeleton/i.test(text) && text.length < 100) {
      const parent = walker.currentNode.parentElement;
      if (parent) {
        const rect = parent.getBoundingClientRect();
        const style = getComputedStyle(parent);
        if (rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden') {
          loadingIndicators.push({
            type: 'text',
            content: text.slice(0, 60),
            tag: parent.tagName,
            classes: parent.className?.toString().slice(0, 60) || undefined,
          });
        }
      }
    }
  }

  // Check for spinning animations
  document.querySelectorAll('[class*="animate-spin"], [class*="spinner"], [class*="loading"]').forEach(el => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    if (rect.width > 0 && rect.height > 0 && style.display !== 'none') {
      loadingIndicators.push({
        type: 'animation',
        tag: el.tagName,
        classes: el.className?.toString().slice(0, 60) || undefined,
      });
    }
  });

  return {
    ok: loadingIndicators.length === 0,
    stuckIndicators: loadingIndicators.length,
    indicators: loadingIndicators.slice(0, 10),
  };
})()


// ============================================================
// 5. OVERFLOW DETECTION
// Finds elements where content overflows its container unintentionally.
// ============================================================
// javascript_tool:
(() => {
  const problems = [];
  const checked = new Set();

  document.querySelectorAll('div, section, main, aside, article, nav').forEach(el => {
    if (checked.has(el)) return;
    checked.add(el);

    const style = getComputedStyle(el);
    if (style.overflow === 'visible' || style.overflow === 'auto' || style.overflow === 'scroll') return;
    if (style.display === 'none') return;

    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    if (el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 2) {
      // Check if overflow is hidden/clipped (intentional)
      if (style.overflow === 'hidden' || style.overflowX === 'hidden' || style.overflowY === 'hidden') return;

      problems.push({
        tag: el.tagName,
        id: el.id || undefined,
        classes: el.className?.toString().slice(0, 80) || undefined,
        clientSize: { w: el.clientWidth, h: el.clientHeight },
        scrollSize: { w: el.scrollWidth, h: el.scrollHeight },
        overflow: { x: el.scrollWidth - el.clientWidth, y: el.scrollHeight - el.clientHeight },
      });
    }
  });

  return {
    ok: problems.length === 0,
    overflowElements: problems.length,
    problems: problems.slice(0, 10),
  };
})()


// ============================================================
// 6. STORE STATE HEALTH
// Verifies the app has loaded data into Zustand stores and key UI elements render.
// ============================================================
// javascript_tool:
(() => {
  const checks = [];

  // Check MetricsBar has values
  const metricsBar = document.querySelector('[class*="metrics"], [class*="MetricsBar"]')
    || document.querySelector('.flex.items-center.gap-4.px-4');
  if (metricsBar) {
    const text = metricsBar.textContent;
    const hasNumbers = /\d+/.test(text);
    checks.push({ name: 'MetricsBar', found: true, hasData: hasNumbers, sample: text?.slice(0, 100) });
  } else {
    checks.push({ name: 'MetricsBar', found: false });
  }

  // Check canvas exists with content
  const canvas = document.querySelector('canvas');
  if (canvas) {
    checks.push({ name: 'Canvas', found: true, width: canvas.width, height: canvas.height, ok: canvas.width > 0 && canvas.height > 0 });
  } else {
    checks.push({ name: 'Canvas', found: false });
  }

  // Check for WebSocket indicator
  const wsEl = document.querySelector('[class*="websocket"], [class*="ws-"]');
  const bodyText = document.body.textContent;
  const hasLiveIndicator = /\bLive\b/.test(bodyText) || /\bConnected\b/.test(bodyText);
  checks.push({ name: 'WebSocket indicator', found: !!wsEl || hasLiveIndicator });

  // Check sidebar exists
  const sidebar = document.querySelector('aside, nav, [class*="sidebar"], [class*="Sidebar"]');
  checks.push({ name: 'Sidebar', found: !!sidebar });

  const passed = checks.filter(c => c.found && (c.ok !== false)).length;
  return {
    summary: `${passed}/${checks.length} UI elements healthy`,
    ok: passed === checks.length,
    checks,
  };
})()


// ============================================================
// 7. SIMULATION API VALIDATION
// POSTs a failure simulation with a real device ID and verifies result shape.
// ============================================================
// javascript_tool:
(async () => {
  const SIM_RESULT_KEYS = [
    'blast_radius', 'blast_radius_pct', 'disconnected_devices',
    'degraded_devices', 'safe_device_ids', 'removed_node_ids',
    'affected_services', 'risk_delta', 'new_components', 'recommendations'
  ];

  // First get a device ID to simulate
  const topoRes = await fetch('http://localhost:8000/api/topology');
  const topo = await topoRes.json();
  if (!topo.devices || topo.devices.length === 0) {
    return { ok: false, error: 'No devices in topology' };
  }

  const targetId = topo.devices[0].id;

  // Run simulation
  const simRes = await fetch('http://localhost:8000/api/simulate/failure', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ remove_nodes: [targetId], remove_edges: [] }),
  });

  const result = await simRes.json();
  const missingKeys = SIM_RESULT_KEYS.filter(k => !(k in result));

  return {
    ok: simRes.ok && missingKeys.length === 0,
    status: simRes.status,
    targetDevice: { id: targetId, hostname: topo.devices[0].hostname },
    missingKeys: missingKeys.length > 0 ? missingKeys : undefined,
    blastRadius: result.blast_radius,
    blastRadiusPct: result.blast_radius_pct,
    disconnected: result.disconnected_devices?.length,
    degraded: result.degraded_devices?.length,
    recommendations: result.recommendations?.length,
  };
})()


// ============================================================
// 8. Z-INDEX AUDIT
// Maps stacking contexts to catch overlay issues.
// ============================================================
// javascript_tool:
(() => {
  const zElements = [];

  document.querySelectorAll('*').forEach(el => {
    const style = getComputedStyle(el);
    const z = parseInt(style.zIndex, 10);
    if (!isNaN(z) && z !== 0 && style.position !== 'static') {
      const rect = el.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        zElements.push({
          tag: el.tagName,
          id: el.id || undefined,
          classes: el.className?.toString().slice(0, 60) || undefined,
          zIndex: z,
          position: style.position,
          bounds: { x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height) },
        });
      }
    }
  });

  // Sort by z-index descending
  zElements.sort((a, b) => b.zIndex - a.zIndex);

  // Check for potential issues: overlapping high z-indexes
  const highZ = zElements.filter(e => e.zIndex >= 40);
  const hasConflicts = highZ.length > 1;

  return {
    ok: true, // Informational — interpret manually
    totalStackingContexts: zElements.length,
    highZElements: highZ.length,
    top10: zElements.slice(0, 10),
    possibleConflicts: hasConflicts ? 'Multiple elements with z-index >= 40 — review for overlap' : 'none',
  };
})()


// ============================================================
// 9. FULL HEALTH SUITE (runs all non-async checks)
// Quick composite check for DOM-based validations.
// ============================================================
// javascript_tool:
(() => {
  const results = {};

  // Visual integrity (simplified)
  let zeroDim = 0;
  document.querySelectorAll('div, section, main, canvas').forEach(el => {
    const style = getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return;
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0 && el.children.length > 0) zeroDim++;
  });
  results.zeroDimElements = zeroDim;

  // Stuck loaders
  let loadingCount = 0;
  document.querySelectorAll('[class*="animate-spin"], [class*="loading"]').forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.width > 0 && getComputedStyle(el).display !== 'none') loadingCount++;
  });
  results.stuckLoaders = loadingCount;

  // Canvas health
  const canvas = document.querySelector('canvas');
  results.canvasExists = !!canvas;
  results.canvasHasSize = canvas ? (canvas.width > 0 && canvas.height > 0) : false;

  // Sidebar
  results.sidebarExists = !!document.querySelector('aside, [class*="sidebar"]');

  // Count visible text nodes with "error" (case insensitive)
  let errorText = 0;
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    if (/\berror\b/i.test(walker.currentNode.textContent) && walker.currentNode.parentElement?.offsetHeight > 0) {
      errorText++;
    }
  }
  results.visibleErrorText = errorText;

  const ok = zeroDim === 0 && loadingCount === 0 && results.canvasExists && results.canvasHasSize;
  return { ok, ...results };
})()
