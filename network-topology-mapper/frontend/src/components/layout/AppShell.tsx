import { useTopologyStore } from '../../stores/topologyStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useSettingsStore } from '../../stores/settingsStore';
import { Moon, Sun, Monitor } from 'lucide-react';
import Sidebar from './Sidebar';

interface Props {
  children: React.ReactNode;
}

export default function AppShell({ children }: Props) {
  const { stats } = useTopologyStore();
  const { connected } = useWebSocket();
  const { theme, setTheme } = useSettingsStore();

  const handleThemeToggle = () => {
    if (theme === 'light') setTheme('dark');
    else if (theme === 'dark') setTheme('system');
    else setTheme('light');
  };

  return (
    <div className="flex h-screen w-screen bg-nd-black text-nd-text-primary overflow-hidden">
      <Sidebar />

      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Header */}
        <header className="flex items-center justify-between px-6 h-12 flex-shrink-0 border-b border-nd-border bg-nd-surface">
          <div className="flex items-center gap-4">
            <h1 className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-primary">Topology</h1>
            <span className="font-mono text-caption text-nd-text-secondary">
              {stats ? `${stats.total_devices} devices` : '\u2014'}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={handleThemeToggle}
              className="p-1.5 rounded-nd-compact hover:bg-nd-surface-raised transition-colors text-nd-text-secondary flex-shrink-0"
              aria-label="Toggle theme"
              title={`Theme: ${theme}`}
            >
              {theme === 'light' ? <Sun size={16} /> : theme === 'dark' ? <Moon size={16} /> : <Monitor size={16} />}
            </button>
            <div className="flex items-center gap-1.5 border-l border-nd-border pl-4">
              <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-nd-success' : 'bg-nd-accent'}`} />
              <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}
