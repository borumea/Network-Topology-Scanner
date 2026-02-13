import { ZoomIn, ZoomOut, Maximize2, Layout, Tag, Activity, Filter, Layers } from 'lucide-react';
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
    activeLayout, setActiveLayout,
    showLabels, setShowLabels,
    showRiskHalos, setShowRiskHalos,
    deviceTypeFilter, toggleDeviceType,
    resetFilters,
  } = useFilterStore();

  const [showLayoutMenu, setShowLayoutMenu] = useState(false);
  const [showFilterMenu, setShowFilterMenu] = useState(false);

  return (
    <div className="absolute bottom-6 right-6 flex flex-col gap-3 z-10">
      {/* Main Control Group */}
      <div className="flex flex-col gap-1 p-1 rounded-2xl bg-bg-secondary/80 backdrop-blur-md border border-white/5 shadow-2xl">
        <div className="relative">
          <button
            onClick={() => { setShowLayoutMenu(!showLayoutMenu); setShowFilterMenu(false); }}
            className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${showLayoutMenu
                ? 'bg-blue-500/20 text-blue-400'
                : 'text-text-secondary hover:text-text-primary hover:bg-white/5'
              }`}
            title="Layout"
          >
            <Layout size={18} />
          </button>

          {/* Layout Menu */}
          {showLayoutMenu && (
            <div className="absolute bottom-0 right-full mr-3 mb-0 bg-bg-secondary/90 backdrop-blur-xl border border-white/10 rounded-2xl py-2 shadow-2xl min-w-[180px] overflow-hidden">
              <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-text-muted">Layout Mode</div>
              {layouts.map((l) => (
                <button
                  key={l.value}
                  onClick={() => { setActiveLayout(l.value); setShowLayoutMenu(false); }}
                  className={`w-full text-left px-4 py-2 text-sm transition-colors flex items-center justify-between ${activeLayout === l.value
                      ? 'text-blue-400 bg-blue-500/10'
                      : 'text-text-secondary hover:text-text-primary hover:bg-white/5'
                    }`}
                >
                  {l.label}
                  {activeLayout === l.value && <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="relative">
          <button
            onClick={() => { setShowFilterMenu(!showFilterMenu); setShowLayoutMenu(false); }}
            className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${deviceTypeFilter.length > 0 || showFilterMenu
                ? 'bg-blue-500/20 text-blue-400'
                : 'text-text-secondary hover:text-text-primary hover:bg-white/5'
              }`}
            title="Filter"
          >
            <Filter size={18} />
            {deviceTypeFilter.length > 0 && (
              <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-blue-400 ring-2 ring-bg-secondary" />
            )}
          </button>

          {/* Filter Menu */}
          {showFilterMenu && (
            <div className="absolute bottom-0 right-full mr-3 mb-0 bg-bg-secondary/90 backdrop-blur-xl border border-white/10 rounded-2xl py-3 px-2 shadow-2xl min-w-[200px]">
              <div className="px-2 pb-2 text-[10px] font-bold uppercase tracking-wider text-text-muted flex justify-between items-center">
                <span>Device Types</span>
                {deviceTypeFilter.length > 0 && (
                  <button onClick={resetFilters} className="text-blue-400 hover:text-blue-300 transition-colors">
                    Reset
                  </button>
                )}
              </div>
              <div className="space-y-0.5">
                {deviceTypes.map((type) => (
                  <label key={type} className="flex items-center gap-3 px-2 py-1.5 rounded-lg hover:bg-white/5 cursor-pointer transition-colors group">
                    <div className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${deviceTypeFilter.includes(type)
                        ? 'bg-blue-500 border-blue-500'
                        : 'border-text-muted group-hover:border-text-secondary'
                      }`}>
                      {deviceTypeFilter.includes(type) && <div className="w-2 h-2 bg-white rounded-sm" />}
                    </div>
                    <span className={`text-sm capitalize transition-colors ${deviceTypeFilter.includes(type) ? 'text-text-primary' : 'text-text-secondary'
                      }`}>{type}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* View Toggles */}
      <div className="flex flex-col gap-1 p-1 rounded-2xl bg-bg-secondary/80 backdrop-blur-md border border-white/5 shadow-2xl">
        <button
          onClick={() => setShowLabels(!showLabels)}
          className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${showLabels
              ? 'text-blue-400 bg-blue-500/10'
              : 'text-text-secondary hover:text-text-primary hover:bg-white/5'
            }`}
          title="Toggle Labels"
        >
          <Tag size={18} />
        </button>
        <button
          onClick={() => setShowRiskHalos(!showRiskHalos)}
          className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${showRiskHalos
              ? 'text-red-400 bg-red-500/10'
              : 'text-text-secondary hover:text-text-primary hover:bg-white/5'
            }`}
          title="Toggle Risk Analysis"
        >
          <Activity size={18} />
        </button>
      </div>

      {/* Zoom Controls */}
      <div className="flex flex-col gap-1 p-1 rounded-2xl bg-bg-secondary/80 backdrop-blur-md border border-white/5 shadow-2xl">
        <button onClick={onZoomIn} className="w-10 h-10 rounded-xl flex items-center justify-center text-text-secondary hover:text-text-primary hover:bg-white/5 transition-all duration-200" title="Zoom In">
          <ZoomIn size={18} />
        </button>
        <button onClick={onZoomOut} className="w-10 h-10 rounded-xl flex items-center justify-center text-text-secondary hover:text-text-primary hover:bg-white/5 transition-all duration-200" title="Zoom Out">
          <ZoomOut size={18} />
        </button>
        <button onClick={onFit} className="w-10 h-10 rounded-xl flex items-center justify-center text-text-secondary hover:text-text-primary hover:bg-white/5 transition-all duration-200 border-t border-white/5" title="Fit to Screen">
          <Maximize2 size={18} />
        </button>
      </div>
    </div>
  );
}
