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
    <div className="flex flex-col h-screen w-screen bg-bg-primary text-text-primary overflow-hidden selection:bg-blue-500/30 selection:text-blue-200">
      {/* Top bar - Glass effect */}
      <header className="flex items-center justify-between px-6 h-16 flex-shrink-0 z-20 relative">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500/20 to-indigo-500/20 border border-blue-500/20 flex items-center justify-center shadow-lg shadow-blue-900/10">
              <span className="text-blue-400 font-bold text-lg">N</span>
            </div>
            <div>
              <h1 className="text-sm font-bold text-text-primary tracking-wide">Network Topology</h1>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-medium text-text-muted uppercase tracking-wider">
                  {stats ? `${stats.total_devices} Devices` : 'Loading...'}
                </span>
                <span className="w-0.5 h-0.5 rounded-full bg-bg-tertiary" />
                <span className={`inline-flex items-center gap-1.5 text-[10px] font-medium ${connected ? 'text-emerald-400' : 'text-red-400'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)] animate-pulse' : 'bg-red-400'}`} />
                  {connected ? 'Live' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => setCommandPaletteOpen(true)}
            className="flex items-center gap-3 px-4 py-2 rounded-xl bg-bg-secondary/50 border border-white/5 text-text-muted text-xs hover:text-text-primary hover:bg-white/5 hover:border-white/10 transition-all duration-200 group shadow-lg"
          >
            <Search size={14} className="group-hover:text-blue-400 transition-colors" />
            <span>Search resources...</span>
            <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded border border-white/10 bg-white/5 px-1.5 font-mono text-[10px] font-medium text-text-muted opacity-100">
              <span className="text-xs">⌘</span>K
            </kbd>
          </button>

          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 p-0.5 shadow-lg shadow-indigo-500/20 cursor-pointer hover:scale-105 transition-transform">
            <div className="w-full h-full rounded-full bg-bg-primary border-2 border-transparent flex items-center justify-center">
              <span className="text-xs font-bold text-white">RB</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden relative z-10">
        <Sidebar />
        <main className="flex-1 overflow-hidden rounded-tl-2xl bg-bg-primary relative ml-2 mt-2 shadow-[inset_2px_2px_20px_rgba(0,0,0,0.5)]">
          {children}
        </main>
      </div>

      <CommandPalette />
    </div>
  );
}
