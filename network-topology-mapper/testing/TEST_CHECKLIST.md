# Test Checklist — Network Topology Mapper

Comprehensive test cases organized by feature area.
Each test specifies the MCP tool, action, and pass/fail criteria.

**Legend:**
- `js` = `javascript_tool`
- `find` = `find`
- `click` = `computer` left_click
- `key` = `computer` key
- `ss` = `computer` screenshot
- `read` = `read_page`
- `net` = `read_network_requests`
- `console` = `read_console_messages`
- `nav` = `navigate`

---

## 1. Pre-flight (6 tests)

| # | Test | Tool | Action | Pass Criteria |
|---|------|------|--------|---------------|
| 1.1 | Backend running | `js` | `fetch('http://localhost:8000/')` | Status 200, body has `version` |
| 1.2 | Health endpoint | `js` | `fetch('/api/health')` | `status === "ok"` |
| 1.3 | Frontend loads | `nav` | Navigate to `http://localhost:3000` | Page loads, not blank |
| 1.4 | No critical console errors | `console` | `onlyErrors: true` | No uncaught exceptions |
| 1.5 | No failed API requests | `net` | `urlPattern: "/api/"` | No 5xx responses |
| 1.6 | WebSocket connects | `console` | `pattern: "WebSocket\|ws"` | Connection established message or no WS errors |

---

## 2. Topology View (20 tests)

| # | Test | Tool | Action | Pass Criteria |
|---|------|------|--------|---------------|
| 2.1 | Canvas renders | `find` | Find `canvas` element | Canvas element exists |
| 2.2 | Canvas has dimensions | `js` | Query canvas width/height | width > 0, height > 0 |
| 2.3 | MetricsBar visible | `find` | Find metrics/device count | Metrics bar with numbers > 0 |
| 2.4 | Device count matches API | `js` | Compare MetricsBar count to `/api/topology/stats` total_devices | Values match |
| 2.5 | Layer toggle — Physical | `find` | Find "Physical" button | Button exists, is active by default |
| 2.6 | Layer toggle — Logical | `click` | Click "Logical" | Graph re-renders, button becomes active |
| 2.7 | Layer toggle — Application | `click` | Click "Application" | Graph re-renders, button becomes active |
| 2.8 | Zoom in button | `click` | Click zoom-in (+) | Graph zooms in |
| 2.9 | Zoom out button | `click` | Click zoom-out (-) | Graph zooms out |
| 2.10 | Fit button | `click` | Click fit-to-screen | Graph fits viewport |
| 2.11 | Layout — Cola | `click` | Select Cola layout | Graph re-layouts with physics |
| 2.12 | Layout — Dagre | `click` | Select Dagre layout | Graph re-layouts hierarchically |
| 2.13 | Layout — Circle | `click` | Select Circle layout | Nodes arrange in circle |
| 2.14 | Layout — Grid | `click` | Select Grid layout | Nodes arrange in grid |
| 2.15 | Filter by device type | `click` | Open filter, toggle a device type off | Nodes of that type disappear |
| 2.16 | Toggle labels | `click` | Click label toggle | Node labels show/hide |
| 2.17 | Toggle risk halos | `click` | Click risk halo toggle | Risk halos show/hide around nodes |
| 2.18 | MiniMap visible | `find` | Find minimap element | MiniMap component rendered |
| 2.19 | Node tooltip on hover | `js` | Dispatch mouseover on a node via Cytoscape | Tooltip appears |
| 2.20 | Screenshot topology | `ss` | Take screenshot | Visual: dark theme, colored nodes, edges visible |

---

## 3. Device Inspector (9 tests)

| # | Test | Tool | Action | Pass Criteria |
|---|------|------|--------|---------------|
| 3.1 | Opens on node click | `js` | Tap first node via Cytoscape | Inspector panel slides in from right |
| 3.2 | Shows hostname | `find` | Find device hostname text | Hostname displayed in header |
| 3.3 | Shows IP address | `find` | Find IP in inspector | IP address visible |
| 3.4 | Shows MAC address | `find` | Find MAC in inspector | MAC address visible |
| 3.5 | Shows risk score | `find` | Find "Risk Score" | Numeric risk score 0-100 |
| 3.6 | Shows open ports | `find` | Find "Open Ports" section | Port list visible (empty OK for some devices) |
| 3.7 | Shows dependencies | `find` | Find "Dependencies" or "Upstream"/"Downstream" | Dependency info visible |
| 3.8 | Simulate Failure button | `find` | Find "Simulate Failure" button | Button exists in inspector |
| 3.9 | Close on background click | `js` | Tap canvas background via Cytoscape | Inspector panel closes |

---

## 4. Sidebar Navigation (14 tests)

| # | Test | Tool | Action | Pass Criteria |
|---|------|------|--------|---------------|
| 4.1 | Sidebar exists | `find` | Find sidebar/nav element | Sidebar present |
| 4.2 | Collapsed by default | `js` | Check sidebar width | Width ~60px when not hovered |
| 4.3 | Expands on hover | `click` | Hover over sidebar area | Width expands to ~220px, labels visible |
| 4.4 | Active indicator | `find` | Find active nav item (left border highlight) | Current view has active styling |
| 4.5 | Nav — Topology | `click` | Click Topology nav item | Topology view loads |
| 4.6 | Nav — Dashboard | `click` | Click Dashboard nav item | Dashboard view loads |
| 4.7 | Nav — Scan | `click` | Click Scan nav item | Scan view loads |
| 4.8 | Nav — Simulate | `click` | Click Simulate nav item | Simulate view loads |
| 4.9 | Nav — Alerts | `click` | Click Alerts nav item | Alerts view loads |
| 4.10 | Nav — Heatmap | `click` | Click Heatmap nav item | Heatmap view loads |
| 4.11 | Nav — Timeline | `click` | Click Timeline nav item | Timeline view loads |
| 4.12 | Nav — Reports | `click` | Click Reports nav item | Reports view loads |
| 4.13 | Nav — Settings | `click` | Click Settings nav item | Settings view loads |
| 4.14 | Alert badge count | `find` | Find alert count badge on Alerts nav | Badge shows number > 0 |

---

## 5. Dashboard View (5 tests)

| # | Test | Tool | Action | Pass Criteria |
|---|------|------|--------|---------------|
| 5.1 | Dashboard loads | `click` | Navigate to Dashboard | Dashboard content renders |
| 5.2 | Device type breakdown | `find` | Find device type chart/cards | Type counts visible (router, switch, etc.) |
| 5.3 | Status breakdown | `find` | Find status chart/counts | Online/offline/degraded counts shown |
| 5.4 | Dependency matrix | `find` | Find DependencyMatrix component | Matrix or dependency visualization present |
| 5.5 | MetricsBar present | `find` | Find metrics bar in dashboard | MetricsBar renders at top |

---

## 6. Scan View (6 tests)

| # | Test | Tool | Action | Pass Criteria |
|---|------|------|--------|---------------|
| 6.1 | Scan view loads | `click` | Navigate to Scan | Scan form visible |
| 6.2 | Target range input | `find` | Find target range input field | Input field present |
| 6.3 | Scan type selector | `find` | Find scan type dropdown/selector | Options: active, passive, snmp, full |
| 6.4 | Intensity slider | `find` | Find intensity control | Range/slider element found |
| 6.5 | Start scan button | `find` | Find start/run scan button | Button present and enabled |
| 6.6 | Scan history | `find` | Find scan history list | Previous scans shown (or empty state) |

---

## 7. Simulate View (11 tests)

| # | Test | Tool | Action | Pass Criteria |
|---|------|------|--------|---------------|
| 7.1 | Simulate view loads | `click` | Navigate to Simulate | Graph + SimulationPanel visible |
| 7.2 | Graph canvas present | `find` | Find canvas in simulate view | Canvas renders |
| 7.3 | SimulationPanel visible | `find` | Find simulation panel | Panel on right side |
| 7.4 | Add target search | `find` | Find device search/add input | Search input in panel |
| 7.5 | Search for device | `click` | Type device name in search | Matching devices appear in results |
| 7.6 | Add target to simulation | `click` | Click a search result | Device added to removal list |
| 7.7 | Run simulation button | `find` | Find "Run" or "Simulate" button | Button present |
| 7.8 | Execute simulation | `click` | Click run button | Results appear: blast radius, disconnected count |
| 7.9 | Blast radius shown | `find` | Find blast radius metric | Numeric blast radius displayed |
| 7.10 | Recommendations shown | `find` | Find recommendations section | At least 1 recommendation |
| 7.11 | Clear simulation | `click` | Click clear/reset button | Simulation results cleared, targets removed |

---

## 8. Alerts View (9 tests)

| # | Test | Tool | Action | Pass Criteria |
|---|------|------|--------|---------------|
| 8.1 | Alerts view loads | `click` | Navigate to Alerts | Graph + AlertFeed visible |
| 8.2 | Alert list populated | `find` | Find alert items | At least 1 alert displayed |
| 8.3 | Alert severity colors | `read` | Read alert elements | Severity indicators (colored borders) present |
| 8.4 | Filter — Critical | `click` | Click Critical severity filter | Only critical alerts shown |
| 8.5 | Filter — High | `click` | Click High severity filter | Only high alerts shown |
| 8.6 | Filter — Clear | `click` | Clear filter | All alerts shown again |
| 8.7 | Acknowledge alert | `click` | Click Acknowledge on an alert | Alert status changes to acknowledged |
| 8.8 | Dismiss alert | `click` | Click Dismiss on an alert | Alert removed or marked dismissed |
| 8.9 | Investigate link | `click` | Click Investigate on alert | Navigates to topology view with device selected |

---

## 9. Heatmap View (4 tests)

| # | Test | Tool | Action | Pass Criteria |
|---|------|------|--------|---------------|
| 9.1 | Heatmap loads | `click` | Navigate to Heatmap | Heatmap content renders |
| 9.2 | Visual content | `ss` | Screenshot | Not blank — heatmap has colored cells/grid |
| 9.3 | Legend visible | `find` | Find color legend/scale | Risk color scale shown |
| 9.4 | Device interaction | `click` | Click a heatmap cell (if interactive) | Tooltip or detail shown |

---

## 10. Timeline View (4 tests)

| # | Test | Tool | Action | Pass Criteria |
|---|------|------|--------|---------------|
| 10.1 | Timeline loads | `click` | Navigate to Timeline | Timeline content renders |
| 10.2 | Visual content | `ss` | Screenshot | Not blank — timeline entries visible |
| 10.3 | Snapshot data | `find` | Find snapshot or changelog entries | At least 1 entry |
| 10.4 | Date information | `find` | Find dates/timestamps | Dates visible in timeline |

---

## 11. Reports View (6 tests)

| # | Test | Tool | Action | Pass Criteria |
|---|------|------|--------|---------------|
| 11.1 | Reports view loads | `click` | Navigate to Reports | Report content renders |
| 11.2 | Resilience score | `find` | Find resilience score | Numeric score displayed |
| 11.3 | Score breakdown | `find` | Find breakdown categories | Connectivity, redundancy, SPOF resistance, path diversity |
| 11.4 | SPOF list | `find` | Find SPOF section | List of single points of failure |
| 11.5 | Report text | `find` | Find report narrative | Text description of resilience |
| 11.6 | Statistics | `find` | Find total devices/connections in report | Stats match API |

---

## 12. Settings View (5 tests)

| # | Test | Tool | Action | Pass Criteria |
|---|------|------|--------|---------------|
| 12.1 | Settings loads | `click` | Navigate to Settings | Settings sections render |
| 12.2 | Scan configuration | `find` | Find scan config section | Scan interval, agent mode options |
| 12.3 | Display settings | `find` | Find display settings | Label, risk halo, animation toggles |
| 12.4 | About section | `find` | Find About section | Version info visible |
| 12.5 | Toggle a setting | `click` | Toggle a display setting | Setting state changes |

---

## 13. Command Palette (9 tests)

| # | Test | Tool | Action | Pass Criteria |
|---|------|------|--------|---------------|
| 13.1 | Opens with Ctrl+K | `key` | Press `ctrl+k` | Palette overlay appears |
| 13.2 | Input focused | `find` | Find search input | Input focused, placeholder visible |
| 13.3 | Search devices | `key` | Type "core" | Device results with hostnames containing "core" |
| 13.4 | Search views | `key` | Clear + type "dashboard" | "Go to Dashboard" navigation action appears |
| 13.5 | Device result icon | `read` | Read result items | Device results have type icons |
| 13.6 | Select device result | `key` | Arrow down + Enter on a device | Navigates to topology, opens DeviceInspector |
| 13.7 | Select nav result | `key` | Type "heatmap" + Enter | Navigates to heatmap view |
| 13.8 | Close with Escape | `key` | Press `Escape` | Palette closes |
| 13.9 | Max 12 results | `key` | Type single letter "s" | At most 12 results shown |

---

## 14. Cross-Cutting Concerns (6 tests)

| # | Test | Tool | Action | Pass Criteria |
|---|------|------|--------|---------------|
| 14.1 | No failed API requests | `net` | Read all `/api/` requests | No 5xx, minimal 4xx |
| 14.2 | No console errors | `console` | `onlyErrors: true, pattern: "Error\|Uncaught"` | Zero uncaught errors |
| 14.3 | No stuck loaders | `js` | Run `stuckLoaderCheck()` from health-checks.js | Zero stuck loading indicators |
| 14.4 | No zero-dimension elements | `js` | Run `visualIntegrityCheck()` from health-checks.js | Zero visible 0x0 elements |
| 14.5 | No unintentional overflow | `js` | Run `overflowDetection()` from health-checks.js | No overflow issues |
| 14.6 | Data shapes valid | `js` | Run data shape validation from health-checks.js | All devices/connections match TypeScript interfaces |

---

## Summary

| Section | Tests | Description |
|---------|-------|-------------|
| 1. Pre-flight | 6 | Backend/frontend alive, no errors |
| 2. Topology View | 20 | Graph, layers, zoom, layout, filters |
| 3. Device Inspector | 9 | Info display, ports, deps, simulate button |
| 4. Sidebar Navigation | 14 | All 9 views, hover, active indicator |
| 5. Dashboard | 5 | Metrics, charts, dependency matrix |
| 6. Scan | 6 | Form, type, intensity, history |
| 7. Simulate | 11 | Targets, run, results, clear |
| 8. Alerts | 9 | List, filters, ack/dismiss, investigate |
| 9. Heatmap | 4 | Renders, legend, interaction |
| 10. Timeline | 4 | Renders, snapshots, dates |
| 11. Reports | 6 | Resilience score, breakdown, SPOFs |
| 12. Settings | 5 | Config sections, toggles |
| 13. Command Palette | 9 | Open, search, select, close |
| 14. Cross-Cutting | 6 | Errors, loaders, overflow, data shapes |
| **TOTAL** | **114** | |
