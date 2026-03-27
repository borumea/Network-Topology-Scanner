import { useEffect, useState, useMemo } from 'react';
import { Search } from 'lucide-react';
import { useSettingsStore } from '../../stores/settingsStore';
import { useTopologyStore } from '../../stores/topologyStore';
import type { ViewType } from '../../types/topology';
import DeviceIcon from '../shared/DeviceIcon';

interface SearchResult {
  type: 'device' | 'action' | 'nav';
  id: string;
  label: string;
  sublabel?: string;
  deviceType?: string;
}

export default function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen } = useSettingsStore();
  const { devices, setCurrentView, selectDevice, setRightPanelContent } = useTopologyStore();
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); setCommandPaletteOpen(!commandPaletteOpen); }
      if (e.key === 'Escape' && commandPaletteOpen) setCommandPaletteOpen(false);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [commandPaletteOpen, setCommandPaletteOpen]);

  const results = useMemo(() => {
    if (!query.trim()) return [];
    const q = query.toLowerCase();
    const items: SearchResult[] = [];

    devices.forEach((d) => {
      if (d.hostname.toLowerCase().includes(q) || d.ip.includes(q) || d.mac.toLowerCase().includes(q) || d.device_type.includes(q)) {
        items.push({ type: 'device', id: d.id, label: d.hostname || d.ip, sublabel: `${d.ip} — ${d.device_type}`, deviceType: d.device_type });
      }
    });

    const navActions: { label: string; view: ViewType }[] = [
      { label: 'Go to Topology', view: 'topology' }, { label: 'Go to Dashboard', view: 'dashboard' },
      { label: 'Go to Heatmap', view: 'heatmap' }, { label: 'Go to Timeline', view: 'timeline' },
      { label: 'Go to Reports', view: 'reports' }, { label: 'Run Scan', view: 'scan' },
      { label: 'Simulate Failure', view: 'simulate' }, { label: 'Show Alerts', view: 'alerts' },
      { label: 'Open Settings', view: 'settings' },
    ];
    navActions.forEach((a) => { if (a.label.toLowerCase().includes(q)) items.push({ type: 'nav', id: a.view, label: a.label }); });

    return items.slice(0, 12);
  }, [query, devices]);

  const handleSelect = (result: SearchResult) => {
    if (result.type === 'device') { setCurrentView('topology'); selectDevice(result.id); setRightPanelContent('device'); }
    else if (result.type === 'nav') setCurrentView(result.id as ViewType);
    setCommandPaletteOpen(false);
    setQuery('');
  };

  if (!commandPaletteOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]">
      <div className="fixed inset-0 bg-black/60" onClick={() => setCommandPaletteOpen(false)} />
      <div className="relative w-[500px] bg-bg-secondary border border-border rounded-lg shadow-2xl overflow-hidden animate-fade-in">
        <div className="flex items-center gap-2.5 px-4 py-3 border-b border-border">
          <Search size={15} className="text-text-muted" />
          <input autoFocus value={query} onChange={(e) => setQuery(e.target.value)}
            placeholder="Search devices, navigate..." className="flex-1 bg-transparent text-text-primary text-sm outline-none placeholder:text-text-muted" />
          <kbd className="text-[10px] text-text-muted bg-bg-tertiary border border-border rounded px-1.5 py-0.5">ESC</kbd>
        </div>
        {results.length > 0 && (
          <div className="max-h-72 overflow-y-auto py-1">
            {results.map((result, i) => (
              <button key={`${result.type}-${result.id}-${i}`} onClick={() => handleSelect(result)}
                className="w-full flex items-center gap-2.5 px-4 py-2 text-left hover:bg-bg-tertiary transition-colors">
                {result.type === 'device' && result.deviceType && <DeviceIcon type={result.deviceType as any} size={15} />}
                {result.type === 'nav' && <Search size={13} className="text-text-muted" />}
                <div className="flex-1 min-w-0">
                  <div className="text-[13px] text-text-primary truncate">{result.label}</div>
                  {result.sublabel && <div className="text-[11px] text-text-muted truncate">{result.sublabel}</div>}
                </div>
                <span className="text-[10px] text-text-muted uppercase">{result.type}</span>
              </button>
            ))}
          </div>
        )}
        {query && results.length === 0 && <div className="px-4 py-6 text-center text-text-muted text-sm">No results</div>}
      </div>
    </div>
  );
}
