import { useState, useEffect } from 'react';
import {
  Map, LayoutDashboard, Search, Zap, Bell, BarChart3, Clock, FileText, Settings, Network,
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
    <aside className="h-full w-[200px] flex-shrink-0 border-r border-border bg-bg-primary flex flex-col">
      {/* Logo */}
      <div className="h-12 flex items-center px-4 border-b border-border gap-2.5">
        <Network size={18} className="text-accent" />
        <span className="text-sm font-semibold">NTS</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-2 px-2 space-y-0.5 overflow-y-auto">
        {navItems.map(({ icon: Icon, label, view }) => {
          const isActive = currentView === view;
          return (
            <button
              key={view}
              onClick={() => handleNavClick(view)}
              className={`
                w-full flex items-center gap-2.5 px-2.5 py-[7px] rounded-md text-[13px] transition-colors relative
                ${isActive
                  ? 'bg-bg-tertiary text-text-primary font-medium'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-secondary'
                }
              `}
            >
              <Icon size={15} className={isActive ? 'text-accent-light' : ''} />
              <span>{label}</span>

              {view === 'alerts' && alertCount > 0 && (
                <span className="ml-auto flex h-4 min-w-[16px] items-center justify-center rounded-full bg-status-offline text-[10px] font-medium text-white px-1">
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
