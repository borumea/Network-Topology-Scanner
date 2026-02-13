import { create } from 'zustand';
import type { LayerType, LayoutType, DeviceType, DeviceStatus } from '../types/topology';

interface FilterState {
  // Layer
  activeLayer: LayerType;
  setActiveLayer: (layer: LayerType) => void;

  // Layout
  activeLayout: LayoutType;
  setActiveLayout: (layout: LayoutType) => void;

  // Filters
  deviceTypeFilter: DeviceType[];
  statusFilter: DeviceStatus[];
  vlanFilter: number[];
  riskMinFilter: number;
  searchQuery: string;
  showLabels: boolean;
  showRiskHalos: boolean;

  // Actions
  toggleDeviceType: (type: DeviceType) => void;
  toggleStatus: (status: DeviceStatus) => void;
  toggleVlan: (vlan: number) => void;
  setRiskMinFilter: (min: number) => void;
  setSearchQuery: (query: string) => void;
  setShowLabels: (show: boolean) => void;
  setShowRiskHalos: (show: boolean) => void;
  resetFilters: () => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  activeLayer: 'physical',
  activeLayout: 'dagre',
  deviceTypeFilter: [],
  statusFilter: [],
  vlanFilter: [],
  riskMinFilter: 0,
  searchQuery: '',
  showLabels: true,
  showRiskHalos: true,

  setActiveLayer: (layer) => set({ activeLayer: layer }),
  setActiveLayout: (layout) => set({ activeLayout: layout }),

  toggleDeviceType: (type) =>
    set((state) => ({
      deviceTypeFilter: state.deviceTypeFilter.includes(type)
        ? state.deviceTypeFilter.filter((t) => t !== type)
        : [...state.deviceTypeFilter, type],
    })),

  toggleStatus: (status) =>
    set((state) => ({
      statusFilter: state.statusFilter.includes(status)
        ? state.statusFilter.filter((s) => s !== status)
        : [...state.statusFilter, status],
    })),

  toggleVlan: (vlan) =>
    set((state) => ({
      vlanFilter: state.vlanFilter.includes(vlan)
        ? state.vlanFilter.filter((v) => v !== vlan)
        : [...state.vlanFilter, vlan],
    })),

  setRiskMinFilter: (min) => set({ riskMinFilter: min }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setShowLabels: (show) => set({ showLabels: show }),
  setShowRiskHalos: (show) => set({ showRiskHalos: show }),

  resetFilters: () =>
    set({
      deviceTypeFilter: [],
      statusFilter: [],
      vlanFilter: [],
      riskMinFilter: 0,
      searchQuery: '',
    }),
}));
