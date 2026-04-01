import { create } from 'zustand';
import type {
  Device, Connection, Dependency, Topology, TopologyStats,
  SimulationResult, SPOF, ViewType,
} from '../types/topology';

interface TopologyState {
  // Data
  devices: Device[];
  connections: Connection[];
  dependencies: Dependency[];
  stats: TopologyStats | null;

  // Selection
  selectedDeviceId: string | null;
  selectedConnectionId: string | null;

  // Simulation
  simulationResult: SimulationResult | null;
  simulationActive: boolean;
  simulationTargets: { nodes: string[]; edges: string[] };

  // SPOFs
  spofs: SPOF[];

  // Navigation
  currentView: ViewType;
  rightPanelContent: 'device' | 'alerts' | 'simulation' | null;

  // Loading
  loading: boolean;
  error: string | null;

  // Actions
  setTopology: (topology: Topology) => void;
  setStats: (stats: TopologyStats) => void;
  setDevices: (devices: Device[]) => void;
  addDevice: (device: Device) => void;
  updateDevice: (device: Device) => void;
  removeDevice: (deviceId: string) => void;
  updateConnection: (connection: Connection) => void;
  selectDevice: (deviceId: string | null) => void;
  selectConnection: (connectionId: string | null) => void;
  setSimulationResult: (result: SimulationResult | null) => void;
  setSimulationActive: (active: boolean) => void;
  addSimulationTarget: (type: 'nodes' | 'edges', id: string) => void;
  removeSimulationTarget: (type: 'nodes' | 'edges', id: string) => void;
  clearSimulationTargets: () => void;
  setSPOFs: (spofs: SPOF[]) => void;
  setCurrentView: (view: ViewType) => void;
  setRightPanelContent: (content: 'device' | 'alerts' | 'simulation' | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useTopologyStore = create<TopologyState>((set) => ({
  devices: [],
  connections: [],
  dependencies: [],
  stats: null,
  selectedDeviceId: null,
  selectedConnectionId: null,
  simulationResult: null,
  simulationActive: false,
  simulationTargets: { nodes: [], edges: [] },
  spofs: [],
  currentView: 'topology',
  rightPanelContent: null,
  loading: false,
  error: null,

  setTopology: (topology) =>
    set({
      devices: topology.devices,
      connections: topology.connections,
      dependencies: topology.dependencies || [],
    }),

  setStats: (stats) => set({ stats }),

  setDevices: (devices) => set({ devices }),

  addDevice: (device) =>
    set((state) => ({
      devices: [...state.devices.filter((d) => d.id !== device.id), device],
    })),

  updateDevice: (device) =>
    set((state) => ({
      devices: state.devices.map((d) => (d.id === device.id ? { ...d, ...device } : d)),
    })),

  removeDevice: (deviceId) =>
    set((state) => ({
      devices: state.devices.filter((d) => d.id !== deviceId),
      connections: state.connections.filter(
        (c) => c.source_id !== deviceId && c.target_id !== deviceId
      ),
      selectedDeviceId: state.selectedDeviceId === deviceId ? null : state.selectedDeviceId,
    })),

  updateConnection: (connection) =>
    set((state) => {
      const exists = state.connections.some((c) => c.id === connection.id);
      if (exists) {
        return {
          connections: state.connections.map((c) =>
            c.id === connection.id ? { ...c, ...connection } : c
          ),
        };
      }
      // Add new connection if it doesn't exist yet
      return { connections: [...state.connections, connection] };
    }),

  selectDevice: (deviceId) =>
    set({
      selectedDeviceId: deviceId,
      selectedConnectionId: null,
      rightPanelContent: deviceId ? 'device' : null,
    }),

  selectConnection: (connectionId) =>
    set({ selectedConnectionId: connectionId }),

  setSimulationResult: (result) => set({ simulationResult: result }),

  setSimulationActive: (active) =>
    set({
      simulationActive: active,
      simulationResult: active ? undefined : null,
    } as any),

  addSimulationTarget: (type, id) =>
    set((state) => ({
      simulationTargets: {
        ...state.simulationTargets,
        [type]: [...state.simulationTargets[type].filter((t) => t !== id), id],
      },
    })),

  removeSimulationTarget: (type, id) =>
    set((state) => ({
      simulationTargets: {
        ...state.simulationTargets,
        [type]: state.simulationTargets[type].filter((t) => t !== id),
      },
    })),

  clearSimulationTargets: () =>
    set({
      simulationTargets: { nodes: [], edges: [] },
      simulationResult: null,
      simulationActive: false,
    }),

  setSPOFs: (spofs) => set({ spofs }),

  setCurrentView: (view) => set({ currentView: view }),

  setRightPanelContent: (content) => set({ rightPanelContent: content }),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),
}));
