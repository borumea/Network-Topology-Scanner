import { useFilterStore } from '../../stores/filterStore';
import type { LayerType } from '../../types/topology';

const layers: { value: LayerType; label: string }[] = [
  { value: 'physical', label: 'Physical' },
  { value: 'logical', label: 'Logical' },
  { value: 'application', label: 'Application' },
];

export default function LayerToggle() {
  const { activeLayer, setActiveLayer } = useFilterStore();

  return (
    <div className="absolute top-3 left-1/2 -translate-x-1/2 z-10 flex bg-bg-secondary border border-border rounded-lg overflow-hidden">
      {layers.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => setActiveLayer(value)}
          className={`px-3 py-1.5 text-[12px] font-medium transition-colors ${
            activeLayer === value
              ? 'bg-accent/10 text-accent-light'
              : 'text-text-muted hover:text-text-secondary hover:bg-bg-tertiary'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
