import { create } from 'zustand';

interface SettingsState {
  sidebarExpanded: boolean;
  commandPaletteOpen: boolean;
  scanScheduleInterval: number;
  snmpPollInterval: number;
  agentMode: 'alert' | 'interactive' | 'autonomous';

  toggleSidebar: () => void;
  setSidebarExpanded: (expanded: boolean) => void;
  setCommandPaletteOpen: (open: boolean) => void;
  setScanScheduleInterval: (interval: number) => void;
  setSnmpPollInterval: (interval: number) => void;
  setAgentMode: (mode: 'alert' | 'interactive' | 'autonomous') => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  sidebarExpanded: false,
  commandPaletteOpen: false,
  scanScheduleInterval: 21600,
  snmpPollInterval: 1800,
  agentMode: 'alert',

  toggleSidebar: () => set((state) => ({ sidebarExpanded: !state.sidebarExpanded })),
  setSidebarExpanded: (expanded) => set({ sidebarExpanded: expanded }),
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
  setScanScheduleInterval: (interval) => set({ scanScheduleInterval: interval }),
  setSnmpPollInterval: (interval) => set({ snmpPollInterval: interval }),
  setAgentMode: (mode) => set({ agentMode: mode }),
}));
