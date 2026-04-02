import { useTopologyStore } from '../../stores/topologyStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import Sidebar from './Sidebar';

interface Props {
  children: React.ReactNode;
}

export default function AppShell({ children }: Props) {
  const { stats } = useTopologyStore();
  const { connected } = useWebSocket();

  return (
    <div className="flex h-screen w-screen bg-nd-black text-nd-text-primary overflow-hidden">
      <Sidebar />

      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Header */}
        <header className="flex items-center px-6 h-12 flex-shrink-0 border-b border-nd-border bg-nd-surface">
          <div className="flex items-center gap-4">
            <h1 className="font-mono text-label uppercase tracking-[0.08em] text-black">Topology</h1>
            <span className="font-mono text-caption text-nd-text-secondary">
              {stats ? `${stats.total_devices} devices` : '\u2014'}
            </span>
            <div className="flex items-center gap-1.5">
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
