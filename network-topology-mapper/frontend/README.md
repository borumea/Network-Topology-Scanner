# Frontend - Network Topology Mapper

React-based frontend for interactive network topology visualization and management.

## Overview

The frontend provides:
- Interactive network graph visualization (Cytoscape.js)
- Real-time topology updates via WebSocket
- Device inspection and management
- Failure simulation interface
- Alert monitoring
- AI-powered resilience reports

## Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **Cytoscape.js** for graph visualization
- **Recharts** for metrics visualization
- **Tailwind CSS** for styling
- **Zustand** for state management
- **Lucide React** for icons

## Architecture

```
src/
├── components/            # React components
│   ├── graph/            # Network graph components
│   │   ├── NetworkCanvas.tsx
│   │   ├── GraphControls.tsx
│   │   ├── LayerToggle.tsx
│   │   ├── MiniMap.tsx
│   │   └── NodeTooltip.tsx
│   ├── panels/           # Side panels
│   │   ├── DeviceInspector.tsx
│   │   ├── AlertFeed.tsx
│   │   ├── SimulationPanel.tsx
│   │   └── ResilienceReport.tsx
│   ├── dashboard/        # Dashboard widgets
│   │   ├── MetricsBar.tsx
│   │   ├── RiskHeatmap.tsx
│   │   └── TimelineView.tsx
│   ├── shared/           # Reusable UI components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── DeviceIcon.tsx
│   │   └── StatusBadge.tsx
│   └── layout/           # Layout components
│       ├── AppShell.tsx
│       ├── Sidebar.tsx
│       └── CommandPalette.tsx
├── hooks/                # Custom React hooks
│   ├── useWebSocket.ts
│   ├── useTopology.ts
│   ├── useSimulation.ts
│   └── useAlerts.ts
├── stores/               # Zustand state stores
│   ├── topologyStore.ts
│   ├── filterStore.ts
│   └── settingsStore.ts
├── lib/                  # Utilities
│   ├── cytoscape-config.ts
│   ├── graph-utils.ts
│   ├── api.ts
│   └── utils.ts
├── types/                # TypeScript types
│   ├── topology.ts
│   ├── device.ts
│   └── api.ts
├── App.tsx               # Root component
└── main.tsx              # Entry point
```

## Quick Start

### Installation

```bash
npm install
```

### Development Server

```bash
npm run dev
```

App runs at http://localhost:3000

### Build for Production

```bash
npm run build
```

Output in `dist/` directory

### Preview Production Build

```bash
npm run preview
```

## Key Components

### Network Canvas

The core graph visualization component.

**Location**: `src/components/graph/NetworkCanvas.tsx`

**Features**:
- Cytoscape.js integration with circular, device-type-colored nodes
- Smooth bezier edge routing with connection-type styling
- Hierarchical (dagre) default layout with gateway at top
- Neighborhood highlighting on node hover (dims non-neighbors to 15% opacity)
- Edge hover tooltips showing connection type, bandwidth, latency, status
- Double-click zoom-to-neighborhood animation
- SPOF node warning rings (red glow)
- Node size tiers: infrastructure (50px), servers (44px), endpoints (36px)
- Zoom, pan, fit controls
- Node selection with blue glow + scale-up

### Device Inspector

Device detail panel that slides in from the right.

**Location**: `src/components/panels/DeviceInspector.tsx`

**Features**:
- Device metadata display
- Risk score visualization
- Connection list
- Dependency tree
- Action buttons

**Usage**:
```tsx
<DeviceInspector
  deviceId={selectedDeviceId}
  onClose={handleClose}
/>
```

### Alert Feed

Real-time alert stream.

**Location**: `src/components/panels/AlertFeed.tsx`

**Features**:
- WebSocket-based real-time updates
- Severity filtering
- Alert acknowledgment
- Auto-scroll to new alerts

**Usage**:
```tsx
<AlertFeed
  filter={{ severity: 'critical' }}
  onAlertClick={handleAlertClick}
/>
```

### Simulation Panel

Failure simulation interface.

**Location**: `src/components/panels/SimulationPanel.tsx`

**Features**:
- Device/link selection for removal
- Impact visualization
- Blast radius calculation
- Mitigation recommendations

**Usage**:
```tsx
<SimulationPanel
  onRunSimulation={handleSimulation}
  onClear={handleClear}
/>
```

## Custom Hooks

### useTopology

Fetch and manage topology data.

```typescript
import { useTopology } from '@/hooks/useTopology';

function MyComponent() {
  const {
    devices,
    connections,
    isLoading,
    error,
    refetch
  } = useTopology();

  // Use topology data...
}
```

### useWebSocket

WebSocket connection and event handling.

```typescript
import { useWebSocket } from '@/hooks/useWebSocket';

function MyComponent() {
  const { isConnected, lastMessage } = useWebSocket({
    onMessage: (event) => {
      if (event.type === 'device_added') {
        // Handle new device
      }
    }
  });
}
```

### useSimulation

Failure simulation state and actions.

```typescript
import { useSimulation } from '@/hooks/useSimulation';

function MyComponent() {
  const {
    simulate,
    result,
    isRunning,
    clear
  } = useSimulation();

  const handleSimulate = async () => {
    const result = await simulate({
      remove_nodes: ['device-id'],
      remove_edges: []
    });
  };
}
```

### useAlerts

Alert management and filtering.

```typescript
import { useAlerts } from '@/hooks/useAlerts';

function MyComponent() {
  const {
    alerts,
    unreadCount,
    acknowledge,
    dismiss
  } = useAlerts({ severity: 'critical' });
}
```

## State Management (Zustand)

### Topology Store

Global topology state.

```typescript
import { useTopologyStore } from '@/stores/topologyStore';

function MyComponent() {
  const devices = useTopologyStore((state) => state.devices);
  const addDevice = useTopologyStore((state) => state.addDevice);
  const updateDevice = useTopologyStore((state) => state.updateDevice);

  // Use store...
}
```

**Store Structure**:
```typescript
interface TopologyStore {
  devices: Device[];
  connections: Connection[];
  selectedDeviceId: string | null;
  layoutMode: LayoutMode;
  addDevice: (device: Device) => void;
  updateDevice: (id: string, updates: Partial<Device>) => void;
  removeDevice: (id: string) => void;
  selectDevice: (id: string | null) => void;
  setLayoutMode: (mode: LayoutMode) => void;
}
```

### Filter Store

Filter and search state.

```typescript
import { useFilterStore } from '@/stores/filterStore';

const filters = useFilterStore((state) => state.filters);
const setFilter = useFilterStore((state) => state.setFilter);

setFilter('device_type', 'switch');
```

## Cytoscape.js Configuration

Graph styling and behavior configured in `src/lib/cytoscape-config.ts`.

### Node Styles

Nodes are circular ellipses with device-type colored fills and tiered sizes:

```typescript
// Base node style
{
  selector: 'node',
  style: {
    shape: 'ellipse',
    width: 36,          // endpoint default
    height: 36,
    'background-color': '#6B7280',
    'border-width': 2,
    label: 'data(label)',
    'text-valign': 'bottom',
    'text-halign': 'center',
    'text-margin-y': 8,
    'font-family': 'Inter, system-ui, sans-serif',
  }
}

// Device types get colored fills and tiered sizes:
// Infrastructure (router, switch, firewall): 50px
// Servers (server, ap): 44px
// Endpoints (workstation, printer, iot): 36px
```

### Edge Styles

Edges use smooth bezier curves with connection-type styling:

```typescript
// Base edge
{
  selector: 'edge',
  style: {
    width: 1.5,
    'line-color': '#334155',
    'curve-style': 'bezier',
    opacity: 0.5,
  }
}

// Connection types: ethernet (solid), fiber (solid/3px/indigo),
// wireless (dashed/violet), vpn (dotted/amber), virtual (dashed/1px)
```

### Interaction Classes

```typescript
// Neighborhood highlighting on hover
'node.highlighted'  // white border glow
'node.dimmed'       // 15% opacity
'edge.highlighted'  // blue, full opacity
'edge.dimmed'       // 8% opacity
'edge.edge-hovered' // light blue feedback on hover
```

### Layout Algorithms

```typescript
// Default: Hierarchical (dagre)
{
  name: 'dagre',
  rankDir: 'TB',
  nodeSep: 100,
  rankSep: 140,
  spacingFactor: 1.2
}

// Force-Directed (cola)
{
  name: 'cola',
  nodeSpacing: 40,
  edgeLength: 200,
  maxSimulationTime: 4000
}

// Also available: circle, grid
```

## Styling

### Tailwind Configuration

Custom colors in `tailwind.config.ts`:

```typescript
export default {
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0F1117',
          secondary: '#1A1D28',
          tertiary: '#242736'
        },
        text: {
          primary: '#E8EAF0',
          secondary: '#8B8FA3',
          muted: '#555B6E'
        },
        status: {
          online: '#10B981',
          offline: '#EF4444',
          degraded: '#F59E0B'
        }
      }
    }
  }
}
```

### CSS Utilities

Use `cn()` utility for conditional classes:

```tsx
import { cn } from '@/lib/utils';

<div className={cn(
  'base-class',
  isActive && 'active-class',
  isDisabled && 'disabled-class'
)} />
```

## API Integration

API client in `src/lib/api.ts`:

```typescript
import { api } from '@/lib/api';

// Fetch topology
const topology = await api.topology.get();

// Trigger scan
const scan = await api.scans.create({
  type: 'full',
  target: '192.168.1.0/24'
});

// Simulate failure
const result = await api.simulation.failure({
  remove_nodes: ['device-id']
});
```

## WebSocket Events

Handle real-time events:

```typescript
useEffect(() => {
  const handleEvent = (event: CustomEvent) => {
    const { type, data } = event.detail;

    switch (type) {
      case 'device_added':
        addDevice(data);
        break;
      case 'device_removed':
        removeDevice(data.id);
        break;
      case 'device_updated':
        updateDevice(data.id, data);
        break;
      case 'connection_change':
        updateConnection(data);
        break;
      case 'alert':
        addAlert(data);
        break;
    }
  };

  window.addEventListener('topology:event', handleEvent);
  return () => window.removeEventListener('topology:event', handleEvent);
}, []);
```

## TypeScript Types

### Device Type

```typescript
interface Device {
  id: string;
  ip: string;
  mac: string;
  hostname: string;
  device_type: DeviceType;
  vendor: string;
  model: string;
  os: string;
  open_ports: number[];
  services: string[];
  first_seen: string;
  last_seen: string;
  vlan_ids: number[];
  subnet: string;
  risk_score: number;
  criticality: 'low' | 'medium' | 'high' | 'critical';
  status: DeviceStatus;
}

type DeviceType = 'router' | 'switch' | 'server' | 'firewall' | 'ap' | 'workstation' | 'iot' | 'unknown';
type DeviceStatus = 'online' | 'offline' | 'degraded';
```

### Connection Type

```typescript
interface Connection {
  id: string;
  source: string;
  target: string;
  connection_type: ConnectionType;
  bandwidth: string;
  latency_ms: number;
  packet_loss_pct: number;
  is_redundant: boolean;
  status: 'active' | 'disabled' | 'degraded' | 'flapping';
}

type ConnectionType = 'ethernet' | 'fiber' | 'wireless' | 'vpn' | 'virtual';
```

## Testing

### Component Tests

```bash
# Run tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

### Example Test

```typescript
import { render, screen } from '@testing-library/react';
import { NetworkCanvas } from './NetworkCanvas';

describe('NetworkCanvas', () => {
  it('renders graph container', () => {
    render(<NetworkCanvas devices={[]} connections={[]} />);
    expect(screen.getByTestId('graph-container')).toBeInTheDocument();
  });

  it('displays devices', () => {
    const devices = [
      { id: '1', hostname: 'device-1', device_type: 'switch' }
    ];
    render(<NetworkCanvas devices={devices} connections={[]} />);
    expect(screen.getByText('device-1')).toBeInTheDocument();
  });
});
```

## Performance Optimization

### Memo and Callbacks

```tsx
import { memo, useMemo, useCallback } from 'react';

export const DeviceList = memo(function DeviceList({ devices }) {
  const sortedDevices = useMemo(
    () => devices.sort((a, b) => b.risk_score - a.risk_score),
    [devices]
  );

  const handleClick = useCallback((id: string) => {
    // Handler logic
  }, []);

  return <div>{/* Render */}</div>;
});
```

### Virtual Scrolling

For large device lists, use virtual scrolling:

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

const virtualizer = useVirtualizer({
  count: devices.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 60
});
```

### Incremental Graph Updates

Update Cytoscape graph incrementally instead of re-rendering:

```typescript
// Add device
cy.add({
  group: 'nodes',
  data: device,
  position: { x: 0, y: 0 }
});

// Update device
cy.getElementById(device.id).data(device);

// Remove device
cy.getElementById(device.id).remove();
```

## Accessibility

- Keyboard navigation support
- ARIA labels on interactive elements
- Focus management
- Color-blind safe color palette
- Screen reader announcements

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Configuration

### Environment Variables

Create `.env.local`:

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_ENABLE_MOCK_DATA=false
```

### Vite Configuration

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
});
```

## Build Optimization

### Code Splitting

```typescript
import { lazy, Suspense } from 'react';

const ResilienceReport = lazy(() => import('./ResilienceReport'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <ResilienceReport />
    </Suspense>
  );
}
```

### Bundle Analysis

```bash
npm run build -- --mode analyze
```

## Troubleshooting

### Common Issues

**"Module not found"**
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear cache: `rm -rf .vite`

**"WebSocket connection failed"**
- Check backend is running
- Verify WS_URL in .env
- Check browser console for errors

**"Graph not rendering"**
- Check Cytoscape.js data format
- Verify devices/connections are valid
- Check browser console for errors

### Debug Mode

Enable React DevTools and check:
- Component re-renders
- State updates
- Props changes

## Deployment

### Build

```bash
npm run build
```

### Serve Static Files

```bash
# Using serve
npx serve dist

# Using nginx
# Copy dist/ to nginx html directory
```

### Environment Variables

Set production environment variables:

```bash
VITE_API_URL=https://api.yourdomcain.com
VITE_WS_URL=wss://api.yourdomain.com/ws
```

## Resources

- [React Documentation](https://react.dev/)
- [Cytoscape.js Documentation](https://js.cytoscape.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [Zustand Documentation](https://docs.pmnd.rs/zustand/)

## Support

For issues or questions:
- Check [documentation](../docs/)
- Open GitHub issue
- Join community channels

---

**Happy coding!** 🎨
