import { ZoomIn, ZoomOut, Maximize2, Layout, Tag, Activity, Filter } from 'lucide-react';
import { useFilterStore } from '../../stores/filterStore';
import { useState } from 'react';
import type { LayoutType, DeviceType } from '../../types/topology';

const layouts: { value: LayoutType; label: string }[] = [
  { value: 'dagre', label: 'Hierarchical' },
  { value: 'cola', label: 'Force-Directed' },
  { value: 'circle', label: 'Circular' },
  { value: 'grid', label: 'Grid' },
];

const deviceTypes: DeviceType[] = [
  'router', 'switch', 'server', 'firewall', 'ap', 'workstation', 'printer', 'iot',
];

const typeColors: Record<string, string> = {
  router: '#818CF8', switch: '#60A5FA', server: '#34D399', firewall: '#FBBF24',
  ap: '#A78BFA', workstation: '#94A3B8', printer: '#FB923C', iot: '#F472B6',
};

interface Props {
  onFit: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
}

export default function GraphControls({ onFit, onZoomIn, onZoomOut }: Props) {
  const {
    activeLayout, setActiveLayout, showLabels, setShowLabels,
    showRiskHalos, setShowRiskHalos, deviceTypeFilter, toggleDeviceType, resetFilters,
  } = useFilterStore();

  const [showLayoutMenu, setShowLayoutMenu] = useState(false);
  const [showFilterMenu, setShowFilterMenu] = useState(false);

  const btnBase = "w-8 h-8 rounded-md flex items-center justify-center transition-colors";
  const btnOff = `${btnBase} text-text-muted hover:text-text-secondary hover:bg-bg-tertiary`;
  const btnOn = `${btnBase} text-accent-light bg-accent/10`;

  return (
    <div className="absolute bottom-4 right-4 flex items-end gap-2 z-10">
      {showLayoutMenu && (
        <div className="bg-bg-secondary border border-border rounded-lg py-1 shadow-lg min-w-[150px] animate-fade-in">
          <div className="px-3 py-1 text-[10px] font-medium uppercase tracking-wider text-text-muted">Layout</div>
          {layouts.map((l) => (
            <button
              key={l.value}
              onClick={() => { setActiveLayout(l.value); setShowLayoutMenu(false); }}
              className={`w-full text-left px-3 py-1.5 text-[13px] transition-colors flex items-center justify-between ${
                activeLayout === l.value ? 'text-accent-light bg-accent/5' : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary'
              }`}
            >
              {l.label}
              {activeLayout === l.value && <div className="w-1.5 h-1.5 rounded-full bg-accent" />}
            </button>
          ))}
        </div>
      )}

      {showFilterMenu && (
        <div className="bg-bg-secondary border border-border rounded-lg py-2 px-1.5 shadow-lg min-w-[170px] animate-fade-in">
          <div className="px-2 pb-1.5 text-[10px] font-medium uppercase tracking-wider text-text-muted flex justify-between">
            <span>Device Types</span>
            {deviceTypeFilter.length > 0 && (
              <button onClick={resetFilters} className="text-accent-light text-[10px]">Clear</button>
            )}
          </div>
          {deviceTypes.map((type) => {
            const active = deviceTypeFilter.includes(type);
            return (
              <label key={type} className="flex items-center gap-2 px-2 py-1 rounded hover:bg-bg-tertiary cursor-pointer">
                <div className={`w-3.5 h-3.5 rounded border flex items-center justify-center ${
                  active ? 'bg-accent border-accent' : 'border-border-light'
                }`}>
                  {active && <svg width="8" height="8" viewBox="0 0 8 8" fill="none"><path d="M1.5 4L3 5.5L6.5 2" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>}
                </div>
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: typeColors[type] }} />
                <span className={`text-[12px] capitalize ${active ? 'text-text-primary' : 'text-text-secondary'}`}>{type}</span>
              </label>
            );
          })}
        </div>
      )}

      <div className="flex items-center bg-bg-secondary border border-border rounded-lg p-0.5 shadow-lg">
        <button onClick={() => { setShowLayoutMenu(!showLayoutMenu); setShowFilterMenu(false); }} className={showLayoutMenu ? btnOn : btnOff} title="Layout"><Layout size={15} /></button>
        <button onClick={() => { setShowFilterMenu(!showFilterMenu); setShowLayoutMenu(false); }} className={`${deviceTypeFilter.length > 0 || showFilterMenu ? btnOn : btnOff} relative`} title="Filter">
          <Filter size={15} />
          {deviceTypeFilter.length > 0 && <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-accent" />}
        </button>
        <div className="w-px h-5 bg-border mx-0.5" />
        <button onClick={() => setShowLabels(!showLabels)} className={showLabels ? btnOn : btnOff} title="Labels"><Tag size={15} /></button>
        <button onClick={() => setShowRiskHalos(!showRiskHalos)} className={showRiskHalos ? `${btnBase} text-status-offline bg-status-offline/10` : btnOff} title="Risk Halos"><Activity size={15} /></button>
        <div className="w-px h-5 bg-border mx-0.5" />
        <button onClick={onZoomIn} className={btnOff} title="Zoom In"><ZoomIn size={15} /></button>
        <button onClick={onZoomOut} className={btnOff} title="Zoom Out"><ZoomOut size={15} /></button>
        <button onClick={onFit} className={btnOff} title="Fit"><Maximize2 size={15} /></button>
      </div>
    </div>
  );
}
