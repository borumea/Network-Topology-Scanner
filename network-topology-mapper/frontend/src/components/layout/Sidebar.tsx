import { useState, useEffect } from 'react';
import {
  Map, LayoutDashboard, Search, Zap, Bell, BarChart3, Clock, FileText, Settings,
} from 'lucide-react';
import { useTopologyStore } from '../../stores/topologyStore';
import type { ViewType } from '../../types/topology';

const navItems: { icon: React.ElementType; label: string; view: ViewType }[] = [
  { icon: Map, label: 'Topology', view: 'topology' },
  { icon: LayoutDashboard, label: 'Dashboard', view: 'dashboard' },
  { icon: Search, label: 'Scan', view: 'scan' },
  { icon: Zap, label: 'Simulate', view: 'simulate' },
  { icon: Bell, label: 'Alerts', view: 'alerts' },
  { icon: BarChart3, label: 'Heatmap', view: 'heatmap' },
  { icon: Clock, label: 'Timeline', view: 'timeline' },
  { icon: FileText, label: 'Reports', view: 'reports' },
  { icon: Settings, label: 'Settings', view: 'settings' },
];

export default function Sidebar() {
  const { currentView, setCurrentView, setRightPanelContent } = useTopologyStore();
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    const handler = () => setAlertCount((prev) => prev + 1);
    window.addEventListener('ws-alert', handler);
    return () => window.removeEventListener('ws-alert', handler);
  }, []);

  const handleNavClick = (view: ViewType) => {
    setCurrentView(view);
    if (view === 'alerts') {
      setRightPanelContent('alerts');
      setAlertCount(0);
    } else if (view === 'simulate') {
      setRightPanelContent('simulation');
    } else if (view === 'topology') {
      setRightPanelContent(null);
    }
  };

  return (
    <aside className="h-full w-[200px] flex-shrink-0 border-r border-nd-border bg-nd-surface flex flex-col">
      {/* Logo */}
      <div className="h-12 flex items-center px-4 border-b border-nd-border gap-2.5">
        <span className="font-display text-heading font-bold text-nd-text-display tracking-tight">NTS</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        {navItems.map(({ icon: Icon, label, view }) => {
          const isActive = currentView === view;
          return (
            <button
              key={view}
              onClick={() => handleNavClick(view)}
              className={`
                w-full flex items-center gap-3 px-3 py-2 rounded-nd-compact transition-colors relative
                font-mono text-label uppercase tracking-[0.08em]
                ${isActive
                  ? 'bg-nd-surface-raised text-nd-text-display'
                  : 'text-nd-text-disabled hover:text-nd-text-primary hover:bg-nd-surface-raised'
                }
              `}
            >
              <Icon size={15} strokeWidth={1.5} className={isActive ? 'text-nd-text-display' : ''} />
              <span>{label}</span>

              {/* Active indicator — dot */}
              {isActive && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-nd-accent" />
              )}

              {/* Alert badge */}
              {view === 'alerts' && alertCount > 0 && (
                <span className="ml-auto flex h-4 min-w-[16px] items-center justify-center rounded-nd-pill bg-nd-accent text-[10px] font-mono font-bold text-white px-1">
                  {alertCount > 9 ? '9+' : alertCount}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
