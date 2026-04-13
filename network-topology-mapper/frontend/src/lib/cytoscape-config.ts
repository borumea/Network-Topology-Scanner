import { getDeviceIcon } from './node-icons';

// Node size tiers by device importance
const NODE_SIZES: Record<string, number> = {
  router: 50,
  switch: 50,
  firewall: 50,
  server: 44,
  ap: 44,
  workstation: 36,
  printer: 36,
  iot: 36,
  unknown: 36,
};

// Nothing light-mode: monochrome graph with status-colored borders only.
// White nodes, dark icons, thin borders. Clean technical diagram.
export const getCytoscapeStylesheet = (isDark: boolean = false): any[] => [
  // ─── Base node: white circle, dark border, icon inside ───
  {
    selector: 'node',
    style: {
      shape: 'ellipse',
      width: 36,
      height: 36,
      'background-color': isDark ? '#1A1A1A' : '#FFFFFF',
      'border-width': 1.5,
      'border-color': isDark ? '#404040' : '#CCCCCC',
      label: 'data(label)',
      'text-valign': 'bottom',
      'text-halign': 'center',
      'text-margin-y': 8,
      'font-size': 10,
      'font-family': "'Space Mono', monospace",
      'text-transform': 'uppercase',
      color: isDark ? '#A3A3A3' : '#666666',
      'text-max-width': '90px',
      'text-wrap': 'ellipsis',
      'text-overflow-wrap': 'anywhere',
      'background-image': getDeviceIcon('unknown' as any, isDark),
      'background-width': 18,
      'background-height': 18,
      'background-position-x': '50%',
      'background-position-y': '50%',
      'background-clip': 'none',
      'background-image-containment': 'over',
      'z-index': 10,
      'overlay-opacity': 0,
      'transition-property': 'opacity, border-color, border-width, width, height',
      'transition-duration': '150ms',
    },
  },

  // ─── Device types: sized tiers with correct icons ───
  ...Object.keys(NODE_SIZES).map((type) => ({
    selector: `node[device_type = "${type}"]`,
    style: {
      width: NODE_SIZES[type] || 36,
      height: NODE_SIZES[type] || 36,
      'background-image': getDeviceIcon(type as any, isDark),
      'background-width': Math.round((NODE_SIZES[type] || 36) * 0.45),
      'background-height': Math.round((NODE_SIZES[type] || 36) * 0.45),
    } as any,
  })),

  // ─── Status: border color is the only color on the graph ───
  {
    selector: 'node[status = "online"]',
    style: {
      'border-color': '#4A9E5C',
      'border-width': 2,
    },
  },
  {
    selector: 'node[status = "offline"]',
    style: {
      'border-color': '#D71921',
      'border-width': 2,
      'border-style': 'dashed',
      opacity: 0.5,
    },
  },
  {
    selector: 'node[status = "degraded"]',
    style: {
      'border-color': '#D4A843',
      'border-width': 2,
      'border-style': 'double',
    },
  },

  // ─── Gateway nodes: slightly larger ───
  {
    selector: 'node[?is_gateway]',
    style: {
      width: 56,
      height: 56,
      'border-width': 2.5,
      'font-weight': 'bold',
      color: isDark ? '#FAFAFA' : '#1A1A1A',
    },
  },

  // ─── SPOF nodes: red border — the accent event ───
  {
    selector: 'node[?isSPOF]',
    style: {
      'border-color': '#D71921',
      'border-width': 3,
    },
  },

  // ─── High risk ───
  {
    selector: 'node[risk_score > 8.0]',
    style: {
      'border-color': '#D71921',
      'border-width': 2.5,
    },
  },
  {
    selector: 'node[risk_score > 5.0][risk_score <= 8.0]',
    style: {
      'border-color': '#D4A843',
      'border-width': 2,
    },
  },

  // ─── Selected state: black ring, no shadow, scale up ───
  {
    selector: ':selected',
    style: {
      'border-width': 3,
      'border-color': isDark ? '#FFFFFF' : '#000000',
      'overlay-opacity': 0,
      width: (ele: any) => (NODE_SIZES[ele.data('device_type')] || 36) + 8,
      height: (ele: any) => (NODE_SIZES[ele.data('device_type')] || 36) + 8,
      'z-index': 100,
      'font-weight': 'bold',
      color: isDark ? '#FAFAFA' : '#1A1A1A',
    },
  },

  // ─── Base edge: thin gray line ───
  {
    selector: 'edge',
    style: {
      width: 1,
      'line-color': isDark ? '#404040' : '#CCCCCC',
      'curve-style': 'bezier',
      'target-arrow-shape': 'none',
      opacity: 0.6,
      'transition-property': 'opacity, line-color, width',
      'transition-duration': '150ms',
    },
  },

  // ─── Edge types: differentiated by line style, not color ───
  {
    selector: 'edge[connection_type = "ethernet"]',
    style: { 'line-style': 'solid' },
  },
  {
    selector: 'edge[connection_type = "fiber"]',
    style: { 'line-style': 'solid', width: 2 },
  },
  {
    selector: 'edge[connection_type = "wireless"]',
    style: { 'line-style': 'dashed', 'line-dash-pattern': [6, 3] },
  },
  {
    selector: 'edge[connection_type = "vpn"]',
    style: { 'line-style': 'dotted' },
  },
  {
    selector: 'edge[connection_type = "virtual"]',
    style: { 'line-style': 'dashed', width: 0.75 },
  },

  // ─── Dependency edges ───
  {
    selector: 'edge[?isDependency]',
    style: {
      'line-style': 'dotted',
      'target-arrow-shape': 'triangle',
      'target-arrow-color': isDark ? '#666666' : '#999999',
      'line-color': isDark ? '#666666' : '#999999',
      opacity: 0.3,
      width: 1,
      'curve-style': 'unbundled-bezier',
    },
  },

  // ─── Flapping edge — the one accent moment ───
  {
    selector: 'edge[status = "flapping"]',
    style: { 'line-color': '#D71921', width: 2 },
  },

  // ─── Disabled edge ───
  {
    selector: 'edge[status = "disabled"]',
    style: { opacity: 0.1, 'line-style': 'dashed' },
  },

  // ─── Redundant edge ───
  {
    selector: 'edge[?is_redundant]',
    style: { 'line-color': '#4A9E5C', opacity: 0.4 },
  },

  // ─── Selected edge ───
  {
    selector: 'edge:selected',
    style: {
      width: 2.5,
      opacity: 1,
      'line-color': isDark ? '#FFFFFF' : '#1A1A1A',
      'z-index': 50,
    },
  },

  // ─── Simulation classes ───
  {
    selector: '.sim-removed',
    style: {
      'background-color': isDark ? '#252525' : '#F0F0F0',
      opacity: 0.3,
      'border-style': 'dashed',
      'border-color': '#D71921',
    },
  },
  {
    selector: '.sim-disconnected',
    style: {
      opacity: 0.5,
      'border-color': '#D71921',
      'border-width': 2.5,
    },
  },
  {
    selector: '.sim-degraded',
    style: {
      'border-color': '#D4A843',
      'border-width': 2.5,
    },
  },
  {
    selector: '.sim-safe',
    style: {
      'border-color': '#4A9E5C',
      'border-width': 2.5,
    },
  },

  // ─── Hover label: show hostname above node ───
  {
    selector: 'node.hovered',
    style: {
      label: (ele: any) => ele.data('hostname') || ele.data('ip') || '',
      'text-valign': 'top',
      'text-margin-y': -10,
      'font-size': 14,
      'font-family': "Space Grotesk, system-ui, sans-serif",
      'font-weight': 'bold',
      color: isDark ? '#FFFFFF' : '#000000',
      'text-max-width': '200px',
      'text-wrap': 'none',
      'z-index': 90,
    },
  },

  // ─── Neighborhood highlight (last to override) ───
  {
    selector: 'node.highlighted',
    style: {
      'border-color': isDark ? '#FFFFFF' : '#000000',
      'border-width': 2.5,
      'z-index': 50,
    },
  },
  {
    selector: 'node.dimmed',
    style: { opacity: 0.12, 'z-index': 1 },
  },
  {
    selector: 'edge.dimmed',
    style: { opacity: 0.06, 'z-index': 1 },
  },
  {
    selector: 'edge.highlighted',
    style: {
      opacity: 1,
      'line-color': isDark ? '#FAFAFA' : '#1A1A1A',
      width: 2,
      'z-index': 50,
    },
  },
  {
    selector: 'edge.edge-hovered',
    style: {
      opacity: 1,
      'line-color': isDark ? '#FFFFFF' : '#000000',
      width: 2.5,
      'z-index': 60,
    },
  },
];

// ─── Layout Options ───

export const dagreLayoutOptions = {
  name: 'dagre',
  rankDir: 'TB',
  nodeSep: 100,
  rankSep: 140,
  ranker: 'network-simplex',
  animate: true,
  animationDuration: 400,
  fit: true,
  padding: 50,
  spacingFactor: 1.2,
};

export const colaLayoutOptions = {
  name: 'cola',
  animate: true,
  animationDuration: 400,
  nodeSpacing: 40,
  edgeLength: 200,
  maxSimulationTime: 4000,
  ungrabifyWhileSimulating: false,
  fit: true,
  padding: 50,
};

export const circleLayoutOptions = {
  name: 'circle',
  animate: true,
  animationDuration: 400,
  fit: true,
  padding: 50,
  avoidOverlap: true,
};

export const gridLayoutOptions = {
  name: 'grid',
  animate: true,
  animationDuration: 400,
  fit: true,
  padding: 50,
  avoidOverlap: true,
  condense: true,
};

export function getLayoutOptions(layout: string) {
  switch (layout) {
    case 'dagre': return dagreLayoutOptions;
    case 'circle': return circleLayoutOptions;
    case 'grid': return gridLayoutOptions;
    default: return colaLayoutOptions;
  }
}
