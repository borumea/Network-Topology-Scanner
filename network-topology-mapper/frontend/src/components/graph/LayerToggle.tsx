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
    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 flex rounded-lg bg-bg-secondary border border-bg-tertiary overflow-hidden">
      {layers.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => setActiveLayer(value)}
          className={`px-4 py-1.5 text-xs font-medium transition-colors ${
            activeLayer === value
              ? 'bg-node-switch/20 text-node-switch'
              : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
