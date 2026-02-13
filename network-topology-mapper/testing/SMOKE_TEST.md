# Smoke Test Procedure

Step-by-step browser-based QA test for the Network Topology Mapper.
Run this when validating a build or after significant changes.

**Prerequisites:** Backend on `:8000`, Frontend on `:3000`
**Tools:** Claude Code MCP browser automation (`javascript_tool`, `read_page`, `find`, `computer`, `navigate`, `screenshot`)

---

## Phase 1: Health Check (Steps 1-6)

### Step 1 — Backend alive
```
Tool: javascript_tool
Code: await fetch('http://localhost:8000/').then(r => r.json())
Pass: response.version === "1.0.0"
```

### Step 2 — Health endpoint
```
Tool: javascript_tool
Code: await fetch('http://localhost:8000/api/health').then(r => r.json())
Pass: response.status === "ok"
```

### Step 3 — Topology endpoint returns data
```
Tool: javascript_tool
Code: await fetch('http://localhost:8000/api/topology').then(r => r.json())
Pass: response.devices.length > 0 && response.connections.length > 0
```

### Step 4 — Stats endpoint returns counts
```
Tool: javascript_tool
Code: await fetch('http://localhost:8000/api/topology/stats').then(r => r.json())
Pass: response.total_devices > 0 && typeof response.type_counts === 'object'
```

### Step 5 — Load frontend
```
Tool: navigate
URL:  http://localhost:3000
Pass: Page loads without blank screen
```

### Step 6 — No critical console errors on load
```
Tool: read_console_messages (onlyErrors: true, pattern: "Error|TypeError|Failed")
Pass: No uncaught exceptions or failed network requests
```

---

## Phase 2: Topology Core (Steps 7-17)

### Step 7 — Graph canvas exists
```
Tool: find
Query: "canvas"
Pass: At least one <canvas> element found
```

### Step 8 — Canvas has dimensions
```
Tool: javascript_tool
Code: (() => { const c = document.querySelector('canvas'); return c ? { w: c.width, h: c.height } : null })()
Pass: width > 0 && height > 0
```

### Step 9 — MetricsBar shows device count
```
Tool: find
Query: "metrics bar" or "total devices"
Pass: A metric shows a number > 0 matching the API total_devices
```

### Step 10 — Screenshot baseline topology
```
Tool: computer (action: screenshot)
Pass: Visual: dark-themed graph with colored nodes visible
```

### Step 11 — Layer toggle exists
```
Tool: find
Query: "Physical" or "Logical" or "Application"
Pass: Layer toggle buttons found
```

### Step 12 — Switch to Logical layer
```
Tool: computer (action: left_click on "Logical" button)
Pass: Graph re-renders (screenshot shows different layout or node arrangement)
```

### Step 13 — Switch to Application layer
```
Tool: computer (action: left_click on "Application" button)
Pass: Graph re-renders
```

### Step 14 — Return to Physical layer
```
Tool: computer (action: left_click on "Physical" button)
Pass: Graph returns to original view
```

### Step 15 — Zoom in
```
Tool: find
Query: "zoom in button" (the + icon in GraphControls)
Tool: computer (action: left_click)
Pass: Graph zooms in (canvas view changes)
```

### Step 16 — Zoom out
```
Tool: find
Query: "zoom out button" (the - icon in GraphControls)
Tool: computer (action: left_click)
Pass: Graph zooms out
```

### Step 17 — Fit to screen
```
Tool: find
Query: "fit" button in GraphControls
Tool: computer (action: left_click)
Pass: Graph fits to viewport
```

---

## Phase 3: Node Interaction (Steps 18-22)

### Step 18 — Click a node on the canvas
```
Strategy: Canvas renders nodes, so we can't directly find DOM elements for them.
Tool: javascript_tool
Code: (() => {
  const cy = document.querySelector('[data-cy]')?.__cy || window.__cy;
  if (!cy) return 'no cytoscape instance found';
  const node = cy.nodes()[0];
  if (!node) return 'no nodes';
  node.emit('tap');
  return { clicked: node.id(), label: node.data('label') };
})()
Fallback: Click near center of canvas element
Pass: DeviceInspector panel appears on the right
```

### Step 19 — DeviceInspector visible
```
Tool: find
Query: "device inspector" or element with class "animate-slide-in-right"
Pass: Inspector panel found with device hostname, IP, MAC visible
```

### Step 20 — Inspector shows risk score
```
Tool: find
Query: "Risk Score" in the inspector panel
Pass: Risk score value is a number between 0 and 100
```

### Step 21 — Inspector shows open ports
```
Tool: find
Query: "Open Ports" section
Pass: Port list visible (may be empty for some devices — that's OK)
```

### Step 22 — Close inspector by clicking background
```
Tool: javascript_tool
Code: (() => {
  const cy = document.querySelector('[data-cy]')?.__cy || window.__cy;
  if (cy) cy.emit('tap');
  return 'tapped background';
})()
Fallback: Click empty area of canvas
Pass: DeviceInspector panel closes
```

---

## Phase 4: Navigate All 9 Views (Steps 23-43)

### Step 23 — Expand sidebar
```
Tool: computer (action: hover over left sidebar area ~x:30)
Pass: Sidebar expands to show labels (220px width)
```

### Step 24 — Navigate to Dashboard
```
Tool: find
Query: "Dashboard" in sidebar
Tool: computer (action: left_click)
Pass: Dashboard view loads with metrics cards
```

### Step 25 — Dashboard has device type breakdown
```
Tool: find
Query: "Device Types" or chart/pie element
Pass: Device type chart or breakdown visible
```

### Step 26 — Dashboard has status breakdown
```
Tool: find
Query: "Status" chart or "online"/"offline" counts
Pass: Status information visible
```

### Step 27 — Screenshot dashboard
```
Tool: computer (action: screenshot)
Pass: Visual check — dashboard layout looks correct
```

### Step 28 — Navigate to Scan
```
Tool: find (sidebar "Scan")
Tool: computer (action: left_click)
Pass: Scan view loads
```

### Step 29 — Scan form visible
```
Tool: find
Query: "Target Range" or scan form input
Pass: Scan configuration form present
```

### Step 30 — Scan has intensity selector
```
Tool: find
Query: "intensity" or range slider
Pass: Intensity control found
```

### Step 31 — Navigate to Simulate
```
Tool: find (sidebar "Simulate")
Tool: computer (action: left_click)
Pass: Simulate view loads with graph + SimulationPanel
```

### Step 32 — Simulation panel visible
```
Tool: find
Query: "Simulate Failure" or "Add Target" or simulation panel
Pass: SimulationPanel found on right side
```

### Step 33 — Navigate to Alerts
```
Tool: find (sidebar "Alerts")
Tool: computer (action: left_click)
Pass: Alerts view loads with graph + AlertFeed
```

### Step 34 — AlertFeed panel visible
```
Tool: find
Query: alert items or "severity" filter
Pass: Alert list visible with severity indicators
```

### Step 35 — Navigate to Heatmap
```
Tool: find (sidebar "Heatmap")
Tool: computer (action: left_click)
Pass: Heatmap view loads
```

### Step 36 — Screenshot heatmap
```
Tool: computer (action: screenshot)
Pass: Visual — heatmap content renders (not blank)
```

### Step 37 — Navigate to Timeline
```
Tool: find (sidebar "Timeline")
Tool: computer (action: left_click)
Pass: Timeline view loads
```

### Step 38 — Screenshot timeline
```
Tool: computer (action: screenshot)
Pass: Visual — timeline content renders
```

### Step 39 — Navigate to Reports
```
Tool: find (sidebar "Reports")
Tool: computer (action: left_click)
Pass: Reports view loads
```

### Step 40 — Reports show resilience score
```
Tool: find
Query: "Resilience" or "Score" in reports
Pass: Resilience report content visible
```

### Step 41 — Navigate to Settings
```
Tool: find (sidebar "Settings")
Tool: computer (action: left_click)
Pass: Settings view loads
```

### Step 42 — Settings has sections
```
Tool: find
Query: "Scan Configuration" or "Display" or "About"
Pass: Settings sections visible
```

### Step 43 — Return to Topology
```
Tool: find (sidebar "Topology" or "Map")
Tool: computer (action: left_click)
Pass: Back to topology graph view
```

---

## Phase 5: Command Palette (Steps 44-49)

### Step 44 — Open command palette with Ctrl+K
```
Tool: computer (action: key, text: "ctrl+k")
Pass: Command palette overlay appears (z-50 overlay with search input)
```

### Step 45 — Command palette input focused
```
Tool: find
Query: "Search devices, actions, navigate"
Pass: Input field found and visible
```

### Step 46 — Search for a device
```
Tool: computer (action: type, text: "core")
Pass: Device results appear (hostnames containing "core")
```

### Step 47 — Search for navigation action
```
Tool: computer (action: key, text: "ctrl+a")  // select all
Tool: computer (action: type, text: "dashboard")
Pass: "Go to Dashboard" action appears in results
```

### Step 48 — Select a navigation result
```
Tool: computer (action: key, text: "Enter")
Pass: Navigates to Dashboard view, command palette closes
```

### Step 49 — Close palette with Escape
```
Tool: computer (action: key, text: "ctrl+k")  // reopen
Tool: computer (action: key, text: "Escape")
Pass: Command palette closes
```

---

## Phase 6: Final Checks (Steps 50-56)

### Step 50 — Check for failed network requests
```
Tool: read_network_requests (urlPattern: "/api/")
Pass: No 4xx or 5xx responses (except expected 404s for missing device IDs)
```

### Step 51 — Check console for errors
```
Tool: read_console_messages (onlyErrors: true)
Pass: No uncaught exceptions, no "Failed to fetch" errors
```

### Step 52 — Run visual integrity check
```
Tool: javascript_tool
Code: [health-checks.js → visualIntegrityCheck()]
Pass: No elements with 0 width and 0 height (excluding hidden/expected elements)
```

### Step 53 — Run stuck loader check
```
Tool: javascript_tool
Code: [health-checks.js → stuckLoaderCheck()]
Pass: No visible "Loading..." text or active spinners
```

### Step 54 — Run overflow detection
```
Tool: javascript_tool
Code: [health-checks.js → overflowDetection()]
Pass: No unintentional overflow on main containers
```

### Step 55 — WebSocket status
```
Tool: find
Query: "Live" or "Connected" WebSocket indicator
Pass: WebSocket shows connected/live status
```

### Step 56 — Final screenshot
```
Tool: computer (action: screenshot)
Pass: App in clean state, no visual glitches
```

---

## Results Template

```
# Smoke Test Results — [DATE]

## Summary
- Total steps: 56
- Passed: X
- Failed: X
- Skipped: X

## Failures
| Step | Description | Expected | Actual | Screenshot |
|------|-------------|----------|--------|------------|
| #    |             |          |        |            |

## Warnings
- [Any non-blocking issues observed]

## Screenshots
- [Links to screenshots taken during test]
```
