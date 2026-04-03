import { useFilterStore } from '../../stores/filterStore';
import type { LayerType } from '../../types/topology';

const layers: { value: LayerType; label: string }[] = [
  { value: 'physical', label: 'Physical' },
  { value: 'logical', label: 'Logical' },
  { value: 'application', label: 'App' },
];

export default function LayerToggle() {
  const { activeLayer, setActiveLayer } = useFilterStore();

  return (
    <div className="absolute top-3 left-1/2 -translate-x-1/2 z-10 flex border border-nd-border-visible rounded-nd-pill overflow-hidden bg-nd-surface">
      {layers.map(({ value, label }) => {
        const isActive = activeLayer === value;
        return (
          <button
            key={value}
            onClick={() => setActiveLayer(value)}
            className={`px-4 py-1.5 font-mono text-label uppercase tracking-[0.08em] transition-colors ${isActive ? 'bg-black text-white' : 'text-nd-text-secondary hover:text-nd-text-primary'}`}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
