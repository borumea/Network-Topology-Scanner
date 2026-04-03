import { STATUS_COLORS } from '../../lib/graph-utils';
import type { DeviceStatus } from '../../types/topology';

interface Props {
  status: DeviceStatus;
  showLabel?: boolean;
  size?: number;
}

export default function StatusBadge({ status, showLabel = true, size = 8 }: Props) {
  const color = STATUS_COLORS[status] || '#999999';

  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="rounded-full" style={{ width: size, height: size, backgroundColor: color }} />
      {showLabel && (
        <span className="font-mono text-label uppercase tracking-[0.08em]" style={{ color }}>
          {status}
        </span>
      )}
    </span>
  );
}
