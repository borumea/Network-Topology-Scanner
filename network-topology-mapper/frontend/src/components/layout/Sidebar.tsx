import { useState, useEffect } from 'react';
import {
  Map, LayoutDashboard, Search, Zap, Bell, BarChart3, Clock, FileText, Settings,
} from 'lucide-react';
import { useTopologyStore } from '../../stores/topologyStore';
import { useSettingsStore } from '../../stores/settingsStore';
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
  const { sidebarExpanded, toggleSidebar } = useSettingsStore();
  const [alertCount, setAlertCount] = useState(0);

  // Track alert count via WebSocket events without fetching
  useEffect(() => {
    const handler = () => {
      setAlertCount((prev) => prev + 1);
    };
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
    <aside
      className="h-full py-4 pl-4"
    >
      <nav
        className="h-full flex flex-col bg-bg-secondary/40 backdrop-blur-xl border border-white/5 rounded-2xl shadow-2xl transition-all duration-300 overflow-hidden"
        style={{ width: sidebarExpanded ? 240 : 72 }}
        onMouseEnter={() => !sidebarExpanded && toggleSidebar()}
        onMouseLeave={() => sidebarExpanded && toggleSidebar()}
      >
        <div className="flex-1 py-3 px-3 space-y-1">
          {navItems.map(({ icon: Icon, label, view }) => {
            const isActive = currentView === view;
            return (
              <button
                key={view}
                onClick={() => handleNavClick(view)}
                className={`
                  w-full flex items-center gap-3 px-3 py-3 rounded-xl text-sm transition-all duration-200 relative group
                  ${isActive
                    ? 'text-white bg-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.15)]'
                    : 'text-text-secondary hover:text-white hover:bg-white/5'
                  }
                `}
                title={label}
              >
                {isActive && (
                  <div className="absolute left-0 w-1 h-8 bg-blue-500 rounded-r-full shadow-[0_0_10px_#3B82F6]" />
                )}

                <div className={`relative z-10 p-1 rounded-lg transition-colors ${isActive ? 'text-blue-400' : 'group-hover:text-white'}`}>
                  <Icon size={20} className="flex-shrink-0" />
                </div>

                <span className={`whitespace-nowrap font-medium transition-all duration-300 overflow-hidden ${sidebarExpanded ? 'opacity-100 max-w-[150px]' : 'opacity-0 max-w-0'
                  } ${isActive ? 'text-white' : ''}`}>
                  {label}
                </span>

                {view === 'alerts' && alertCount > 0 && (
                  <span className={`absolute top-3 right-3 flex h-5 min-w-[20px] items-center justify-center rounded-full bg-red-500/80 text-[10px] font-bold text-white shadow-lg transition-all duration-300 ${!sidebarExpanded ? 'right-2 top-2' : ''
                    }`}>
                    {alertCount > 9 ? '9+' : alertCount}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </nav>
    </aside>
  );
}
