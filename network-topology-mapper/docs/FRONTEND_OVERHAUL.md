# Frontend Visual Overhaul Documentation

## Overview
This document outlines the **Graph Visualization Overhaul** of the Network Topology Mapper. The graph has been redesigned from oversized rectangular card nodes with taxi routing into a clean, circular-node hierarchical view with rich interactivity.

## Design Philosophy
-   **Layout**: Hierarchical (dagre) by default, top-down flow (Gateway -> Core -> Access -> Endpoints).
-   **Nodes**: Circular ellipses with device-type colored fills and centered icons. Sized by importance tier.
-   **Edges**: Smooth bezier curves with connection-type styling and bandwidth-scaled widths.
-   **Interactivity**: Neighborhood highlighting on hover, edge tooltips, double-click zoom-to-neighborhood.
-   **Aesthetics**: Clean sans-serif labels below nodes, subtle transitions, SPOF warning rings.

## Color Palette
Device-type colors are applied as full node background fills (not just borders):
-   **Router**: `#818CF8` (Indigo-400)
-   **Switch**: `#60A5FA` (Blue-400)
-   **Server**: `#34D399` (Emerald-400)
-   **Firewall**: `#FBBF24` (Amber-400)
-   **Access Point**: `#A78BFA` (Violet-400)
-   **Workstation**: `#94A3B8` (Slate-400)
-   **IoT**: `#F472B6` (Pink-400)
-   **Printer**: `#FB923C` (Orange-400)

## Node Design
-   **Shape**: Ellipse (circular)
-   **Size tiers**:
    -   Infrastructure (router, switch, firewall): 50px
    -   Servers (server, ap): 44px
    -   Endpoints (workstation, printer, iot): 36px
-   **Icons**: Centered SVG icons with dark contrasting stroke colors per device type
-   **Labels**: Below node (`text-valign: bottom`), Inter/system-ui font, 11px
-   **Gateway nodes**: 56px with bold label

## Edge Design
-   **Curve style**: `bezier` (smooth curves)
-   **Base**: 1.5px width, `#334155` at 50% opacity
-   **Connection types**:
    -   Ethernet: solid, slate
    -   Fiber: solid, 3px, indigo
    -   Wireless: dashed, violet
    -   VPN: dotted, amber
    -   Virtual: dashed, 1px, slate
-   **Dependency edges**: Dotted with triangle arrow, violet, unbundled-bezier

## Status Indicators
-   **Online**: Green border (`#34D399`)
-   **Offline**: Red dashed border + dimmed opacity (0.6)
-   **Degraded**: Amber double border
-   **SPOF**: Red shadow glow (`shadow-blur: 20`, `shadow-color: #EF4444`)

## Interactivity

### Neighborhood Highlighting (Node Hover)
When hovering a node, all connected nodes and edges receive `.highlighted` class (white border glow), and everything else receives `.dimmed` class (15% opacity). On mouseout, all classes are cleared.

### Edge Tooltip (Edge Hover)
Hovering an edge shows a compact tooltip with:
-   Connection type icon and label
-   Bandwidth
-   Latency (ms)
-   Status with color indicator
-   Redundancy flag

### Double-Click Zoom
Double-clicking a node animates the camera to fit the selected node and its 1-hop neighbors with 80px padding.

### Selected State
Selected nodes get a white border + blue shadow glow + 8px scale-up.

## Hierarchical Structure (Backend)
The backend (`mock_data.py`) assigns a specific `tier` to every device to enforce vertical layering:
-   **Tier 0**: Gateway Router
-   **Tier 1**: Firewalls
-   **Tier 2**: Core Switching
-   **Tier 3**: Server/Distribution Switching
-   **Tier 4**: Access Switching / Servers
-   **Tier 5**: Workstations, Printers, IoT

## Layout Configuration
-   **Default layout**: `dagre` (hierarchical)
-   **Dagre settings**: `rankDir: TB`, `nodeSep: 100`, `rankSep: 140`, `spacingFactor: 1.2`
-   **Available layouts**: Hierarchical, Force-Directed (cola), Circular, Grid

## Component Updates

### `cytoscape-config.ts`
-   Ellipse nodes with device-type colored fills and tiered sizes
-   Bezier edges with connection-type styling
-   Highlight/dimmed/edge-hovered CSS classes
-   SPOF red shadow glow
-   Selected state with blue glow and scale-up
-   Increased dagre spacing (nodeSep: 100, rankSep: 140)

### `node-icons.ts`
-   Device-type-specific dark stroke colors for contrast against colored node fills
-   Pre-built icon cache per device type for performance

### `NetworkCanvas.tsx`
-   Neighborhood highlighting on node hover (dimmed + highlighted classes)
-   Edge hover tooltip via `edge-hover` CustomEvent
-   Edge hover visual feedback (`.edge-hovered` class)
-   Double-click zoom-to-neighborhood animation
-   `cyReady` counter forces MiniMap refresh on data changes

### `NodeTooltip.tsx`
-   Dual tooltip mode: node tooltips and edge tooltips
-   Edge tooltip shows connection type with icon, bandwidth, latency, status
-   Mutual exclusion: showing one hides the other

### `GraphControls.tsx`
-   Hierarchical layout listed first (since it's the new default)

### `MiniMap.tsx`
-   Nodes drawn with device-type color fills (not border-color)
-   Dot radius increased from 2 to 3 for visibility
-   Update interval reduced from 1000ms to 500ms

### `filterStore.ts`
-   Default layout changed from `cola` to `dagre`

## Verification
-   Verify that the graph flows clearly from top to bottom with dagre layout
-   Nodes should be circular with device-type colored fills
-   Hovering a node should dim everything except its neighborhood
-   Hovering an edge should show connection details tooltip
-   Double-clicking a node should zoom to its neighborhood
-   SPOF nodes should have red glow rings
-   TypeScript compiles clean: `npx tsc --noEmit`
