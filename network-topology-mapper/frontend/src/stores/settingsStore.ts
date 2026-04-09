import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type ThemeMode = 'light' | 'dark' | 'system';

interface SettingsState {
  theme: ThemeMode;
  sidebarExpanded: boolean;
  commandPaletteOpen: boolean;
  scanScheduleInterval: number;
  snmpPollInterval: number;
  agentMode: 'alert' | 'interactive' | 'autonomous';

  setTheme: (theme: ThemeMode) => void;
  toggleSidebar: () => void;
  setSidebarExpanded: (expanded: boolean) => void;
  setCommandPaletteOpen: (open: boolean) => void;
  setScanScheduleInterval: (interval: number) => void;
  setSnmpPollInterval: (interval: number) => void;
  setAgentMode: (mode: 'alert' | 'interactive' | 'autonomous') => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      theme: 'system',
      sidebarExpanded: false,
      commandPaletteOpen: false,
      scanScheduleInterval: 21600,
      snmpPollInterval: 1800,
      agentMode: 'alert',

      setTheme: (theme: ThemeMode) => set({ theme }),
      toggleSidebar: () => set((state: SettingsState) => ({ sidebarExpanded: !state.sidebarExpanded })),
      setSidebarExpanded: (expanded: boolean) => set({ sidebarExpanded: expanded }),
      setCommandPaletteOpen: (open: boolean) => set({ commandPaletteOpen: open }),
      setScanScheduleInterval: (interval: number) => set({ scanScheduleInterval: interval }),
      setSnmpPollInterval: (interval: number) => set({ snmpPollInterval: interval }),
      setAgentMode: (mode: 'alert' | 'interactive' | 'autonomous') => set({ agentMode: mode }),
    }),
    {
      name: 'settings-store',
    }
  )
);
