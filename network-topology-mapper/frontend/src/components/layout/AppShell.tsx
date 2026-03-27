import { useSettingsStore } from '../../stores/settingsStore';
import { useTopologyStore } from '../../stores/topologyStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { Search } from 'lucide-react';
import Sidebar from './Sidebar';
import CommandPalette from './CommandPalette';

interface Props {
  children: React.ReactNode;
}

export default function AppShell({ children }: Props) {
  const { setCommandPaletteOpen } = useSettingsStore();
  const { stats } = useTopologyStore();
  const { connected } = useWebSocket();

  return (
    <div className="flex h-screen w-screen bg-bg-primary text-text-primary overflow-hidden">
      <Sidebar />

      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Header */}
        <header className="flex items-center justify-between px-6 h-12 flex-shrink-0 border-b border-border">
          <div className="flex items-center gap-3">
            <h1 className="text-sm font-semibold text-text-primary">Topology</h1>
            <span className="text-xs text-text-muted">
              {stats ? `${stats.total_devices} devices` : '—'}
            </span>
            <div className="flex items-center gap-1.5 ml-1">
              <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-status-online' : 'bg-status-offline'}`} />
              <span className="text-[11px] text-text-muted">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-bg-tertiary border border-border text-text-muted text-xs hover:text-text-secondary hover:border-border-light transition-colors"
            >
              <Search size={13} />
              <span>Search...</span>
              <kbd className="hidden sm:inline text-[10px] text-text-muted bg-bg-primary border border-border rounded px-1 py-px ml-2">⌘K</kbd>
            </button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-hidden">
          {children}
        </main>
      </div>

      <CommandPalette />
    </div>
  );
}
