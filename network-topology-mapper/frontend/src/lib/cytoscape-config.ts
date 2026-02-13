import { DEVICE_TYPE_COLORS, CONNECTION_TYPE_COLORS } from './graph-utils';
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

export const cytoscapeStylesheet: any[] = [
  // ─── Base node: circular with clean label below ───
  {
    selector: 'node',
    style: {
      shape: 'ellipse',
      width: 36,
      height: 36,
      'background-color': '#6B7280',
      'border-width': 2,
      'border-color': '#475569',
      label: 'data(label)',
      'text-valign': 'bottom',
      'text-halign': 'center',
      'text-margin-y': 8,
      'font-size': 11,
      'font-family': 'Inter, system-ui, sans-serif',
      color: '#CBD5E1',
      'text-max-width': '90px',
      'text-wrap': 'ellipsis',
      'text-overflow-wrap': 'anywhere',
      'background-image': getDeviceIcon('unknown' as any),
      'background-width': 20,
      'background-height': 20,
      'background-position-x': '50%',
      'background-position-y': '50%',
      'background-clip': 'none',
      'background-image-containment': 'over',
      'z-index': 10,
      'overlay-opacity': 0,
      'transition-property': 'opacity, border-color, border-width, shadow-blur, shadow-opacity, width, height',
      'transition-duration': '200ms',
    },
  },

  // ─── Device type: color fills, icons, and tiered sizes ───
  ...Object.entries(DEVICE_TYPE_COLORS).map(([type, color]) => ({
    selector: `node[device_type = "${type}"]`,
    style: {
      'background-color': color,
      'border-color': color,
      width: NODE_SIZES[type] || 36,
      height: NODE_SIZES[type] || 36,
      'background-image': getDeviceIcon(type as any),
      'background-width': Math.round((NODE_SIZES[type] || 36) * 0.5),
      'background-height': Math.round((NODE_SIZES[type] || 36) * 0.5),
      'background-position-x': '50%',
      'background-position-y': '50%',
    } as any,
  })),

  // ─── Status indicators ───
  {
    selector: 'node[status = "online"]',
    style: {
      'border-color': '#34D399',
      'border-width': 2.5,
    },
  },
  {
    selector: 'node[status = "offline"]',
    style: {
      'border-color': '#EF4444',
      'border-width': 3,
      'border-style': 'dashed',
      opacity: 0.6,
    },
  },
  {
    selector: 'node[status = "degraded"]',
    style: {
      'border-color': '#F59E0B',
      'border-width': 3,
      'border-style': 'double',
    },
  },

  // ─── Gateway nodes: slightly larger with diamond border accent ───
  {
    selector: 'node[?is_gateway]',
    style: {
      width: 56,
      height: 56,
      'border-width': 3,
      'font-weight': 'bold',
      color: '#F0F4F8',
    },
  },

  // ─── SPOF nodes: pulsing red warning ring ───
  {
    selector: 'node[?isSPOF]',
    style: {
      'shadow-blur': 20,
      'shadow-color': '#EF4444',
      'shadow-opacity': 0.7,
      'border-color': '#EF4444',
      'border-width': 3,
    },
  },

  // ─── Risk scores ───
  {
    selector: 'node[risk_score > 8.0]',
    style: {
      'shadow-blur': 25,
      'shadow-color': '#EF4444',
      'shadow-opacity': 0.6,
    },
  },
  {
    selector: 'node[risk_score > 5.0][risk_score <= 8.0]',
    style: {
      'shadow-blur': 15,
      'shadow-color': '#F97316',
      'shadow-opacity': 0.4,
    },
  },

  // ─── Selected state: white ring + blue glow + scale up ───
  {
    selector: ':selected',
    style: {
      'border-width': 3,
      'border-color': '#ffffff',
      'shadow-blur': 30,
      'shadow-color': '#3B82F6',
      'shadow-opacity': 0.7,
      'overlay-opacity': 0,
      width: (ele: any) => (NODE_SIZES[ele.data('device_type')] || 36) + 8,
      height: (ele: any) => (NODE_SIZES[ele.data('device_type')] || 36) + 8,
      'z-index': 100,
      'font-weight': 'bold',
      color: '#F0F4F8',
    },
  },

  // ─── Base edge style: smooth bezier ───
  {
    selector: 'edge',
    style: {
      width: 1.5,
      'line-color': '#334155',
      'curve-style': 'bezier',
      'target-arrow-shape': 'none',
      opacity: 0.5,
      'transition-property': 'opacity, line-color, width',
      'transition-duration': '200ms',
    },
  },

  // ─── Edge connection types ───
  {
    selector: 'edge[connection_type = "ethernet"]',
    style: {
      'line-color': CONNECTION_TYPE_COLORS.ethernet,
      'line-style': 'solid',
    },
  },
  {
    selector: 'edge[connection_type = "fiber"]',
    style: {
      'line-color': CONNECTION_TYPE_COLORS.fiber,
      'line-style': 'solid',
      width: 3,
    },
  },
  {
    selector: 'edge[connection_type = "wireless"]',
    style: {
      'line-color': CONNECTION_TYPE_COLORS.wireless,
      'line-style': 'dashed',
      'line-dash-pattern': [6, 3],
    },
  },
  {
    selector: 'edge[connection_type = "vpn"]',
    style: {
      'line-color': CONNECTION_TYPE_COLORS.vpn,
      'line-style': 'dotted',
    },
  },
  {
    selector: 'edge[connection_type = "virtual"]',
    style: {
      'line-color': CONNECTION_TYPE_COLORS.virtual,
      'line-style': 'dashed',
      width: 1,
    },
  },

  // ─── Dependency edges ───
  {
    selector: 'edge[?isDependency]',
    style: {
      'line-style': 'dotted',
      'target-arrow-shape': 'triangle',
      'target-arrow-color': '#A78BFA',
      'line-color': '#A78BFA',
      opacity: 0.3,
      width: 1.5,
      'curve-style': 'unbundled-bezier',
    },
  },

  // ─── Flapping edge ───
  {
    selector: 'edge[status = "flapping"]',
    style: {
      'line-color': '#F87171',
      width: 3,
    },
  },

  // ─── Disabled edge ───
  {
    selector: 'edge[status = "disabled"]',
    style: {
      opacity: 0.1,
      'line-style': 'dashed',
    },
  },

  // ─── Redundant edge ───
  {
    selector: 'edge[?is_redundant]',
    style: {
      'line-color': '#34D399',
    },
  },

  // ─── Selected edge ───
  {
    selector: 'edge:selected',
    style: {
      width: 4,
      opacity: 1,
      'line-color': '#60A5FA',
      'z-index': 50,
    },
  },

  // ─── Simulation classes ───
  {
    selector: '.sim-removed',
    style: {
      'background-color': '#F87171',
      opacity: 0.3,
      'border-style': 'dashed',
      'border-color': '#F87171',
    },
  },
  {
    selector: '.sim-disconnected',
    style: {
      'background-color': '#7F1D1D',
      opacity: 0.6,
      'border-color': '#EF4444',
      'shadow-blur': 15,
      'shadow-color': '#EF4444',
    },
  },
  {
    selector: '.sim-degraded',
    style: {
      'border-color': '#FBBF24',
      'shadow-blur': 10,
      'shadow-color': '#FBBF24',
    },
  },
  {
    selector: '.sim-safe',
    style: {
      'background-color': '#065F46',
      'border-color': '#34D399',
      'shadow-blur': 10,
      'shadow-color': '#34D399',
    },
  },

  // ─── Neighborhood highlight classes (last to override everything) ───
  {
    selector: 'node.highlighted',
    style: {
      'border-color': '#ffffff',
      'shadow-blur': 20,
      'shadow-color': '#ffffff',
      'shadow-opacity': 0.4,
      'z-index': 50,
    },
  },
  {
    selector: 'node.dimmed',
    style: {
      opacity: 0.15,
      'z-index': 1,
    },
  },
  {
    selector: 'edge.dimmed',
    style: {
      opacity: 0.08,
      'z-index': 1,
    },
  },
  {
    selector: 'edge.highlighted',
    style: {
      opacity: 1,
      'line-color': '#60A5FA',
      width: 3,
      'z-index': 50,
    },
  },
  {
    selector: 'edge.edge-hovered',
    style: {
      opacity: 1,
      'line-color': '#93C5FD',
      width: 3.5,
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
  animationDuration: 500,
  fit: true,
  padding: 50,
  spacingFactor: 1.2,
};

export const colaLayoutOptions = {
  name: 'cola',
  animate: true,
  animationDuration: 500,
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
  animationDuration: 500,
  fit: true,
  padding: 50,
  avoidOverlap: true,
};

export const gridLayoutOptions = {
  name: 'grid',
  animate: true,
  animationDuration: 500,
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
