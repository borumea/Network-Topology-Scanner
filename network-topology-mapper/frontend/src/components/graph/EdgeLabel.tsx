import type { Connection } from '../../types/topology';
import { CONNECTION_TYPE_COLORS } from '../../lib/graph-utils';

interface Props {
  connection: Connection;
}

export default function EdgeLabel({ connection }: Props) {
  const color = CONNECTION_TYPE_COLORS[connection.connection_type] || '#475569';

  return (
    <div className="inline-flex items-center gap-2 px-2 py-1 rounded bg-bg-secondary border border-bg-tertiary text-xs">
      <span
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: color }}
      />
      <span className="text-text-secondary capitalize">{connection.connection_type}</span>
      {connection.bandwidth && (
        <span className="text-text-muted">{connection.bandwidth}</span>
      )}
      {connection.latency_ms > 0 && (
        <span className="text-text-muted">{connection.latency_ms}ms</span>
      )}
      {connection.status === 'flapping' && (
        <span className="text-risk-critical font-medium">FLAPPING</span>
      )}
    </div>
  );
}
