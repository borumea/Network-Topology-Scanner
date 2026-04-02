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

  const btnBase = "w-8 h-8 rounded-nd-technical flex items-center justify-center transition-colors";
  const btnOff = `${btnBase} text-nd-text-disabled hover:text-nd-text-primary hover:bg-nd-surface-raised`;
  const btnOn = `${btnBase} text-nd-text-display bg-nd-surface-raised`;

  return (
    <div className="absolute bottom-4 right-4 flex items-end gap-2 z-10">
      {/* Layout dropdown */}
      {showLayoutMenu && (
        <div className="bg-white border border-nd-border-visible rounded-nd-compact py-1 min-w-[150px] animate-fade-in z-30" style={{ boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
          <div className="px-3 py-1 font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">Layout</div>
          {layouts.map((l) => (
            <button
              key={l.value}
              onClick={() => { setActiveLayout(l.value); setShowLayoutMenu(false); }}
              className={`w-full text-left px-3 py-1.5 text-body-sm font-sans transition-colors flex items-center justify-between ${
                activeLayout === l.value ? 'text-nd-text-display bg-nd-surface-raised' : 'text-nd-text-secondary hover:text-nd-text-primary hover:bg-nd-surface-raised'
              }`}
            >
              {l.label}
              {activeLayout === l.value && <div className="w-1.5 h-1.5 rounded-full bg-nd-accent" />}
            </button>
          ))}
        </div>
      )}

      {/* Filter dropdown */}
      {showFilterMenu && (
        <div className="bg-white border border-nd-border-visible rounded-nd-compact py-2 px-1.5 min-w-[170px] animate-fade-in z-30" style={{ boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
          <div className="px-2 pb-1.5 font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled flex justify-between">
            <span>Device Types</span>
            {deviceTypeFilter.length > 0 && (
              <button onClick={resetFilters} className="text-nd-accent text-[10px] font-mono uppercase">Clear</button>
            )}
          </div>
          {deviceTypes.map((type) => {
            const active = deviceTypeFilter.includes(type);
            return (
              <label key={type} className="flex items-center gap-2 px-2 py-1 rounded-nd-technical hover:bg-nd-surface-raised cursor-pointer">
                <div className={`w-3.5 h-3.5 rounded-nd-technical border flex items-center justify-center ${
                  active ? 'bg-black border-black' : 'border-nd-border-visible'
                }`}>
                  {active && <svg width="8" height="8" viewBox="0 0 8 8" fill="none"><path d="M1.5 4L3 5.5L6.5 2" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>}
                </div>
                <span className={`font-mono text-label uppercase tracking-[0.06em] ${active ? 'text-nd-text-primary' : 'text-nd-text-secondary'}`}>{type}</span>
              </label>
            );
          })}
        </div>
      )}

      {/* Control bar */}
      <div className="flex items-center bg-nd-surface border border-nd-border-visible rounded-nd-compact p-0.5">
        <button onClick={() => { setShowLayoutMenu(!showLayoutMenu); setShowFilterMenu(false); }} className={showLayoutMenu ? btnOn : btnOff} title="Layout"><Layout size={15} strokeWidth={1.5} /></button>
        <button onClick={() => { setShowFilterMenu(!showFilterMenu); setShowLayoutMenu(false); }} className={`${deviceTypeFilter.length > 0 || showFilterMenu ? btnOn : btnOff} relative`} title="Filter">
          <Filter size={15} strokeWidth={1.5} />
          {deviceTypeFilter.length > 0 && <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-nd-accent" />}
        </button>
        <div className="w-px h-5 bg-nd-border mx-0.5" />
        <button onClick={() => setShowLabels(!showLabels)} className={showLabels ? btnOn : btnOff} title="Labels"><Tag size={15} strokeWidth={1.5} /></button>
        <button onClick={() => setShowRiskHalos(!showRiskHalos)} className={showRiskHalos ? `${btnBase} text-nd-accent bg-nd-accent/10` : btnOff} title="Risk"><Activity size={15} strokeWidth={1.5} /></button>
        <div className="w-px h-5 bg-nd-border mx-0.5" />
        <button onClick={onZoomIn} className={btnOff} title="Zoom In"><ZoomIn size={15} strokeWidth={1.5} /></button>
        <button onClick={onZoomOut} className={btnOff} title="Zoom Out"><ZoomOut size={15} strokeWidth={1.5} /></button>
        <button onClick={onFit} className={btnOff} title="Fit"><Maximize2 size={15} strokeWidth={1.5} /></button>
      </div>
    </div>
  );
}
