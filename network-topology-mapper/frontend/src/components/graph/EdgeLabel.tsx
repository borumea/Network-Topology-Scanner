import type { Connection } from '../../types/topology';

interface Props {
  connection: Connection;
}

export default function EdgeLabel({ connection }: Props) {
  return (
    <div className="inline-flex items-center gap-2 px-2 py-1 rounded-nd-technical bg-nd-surface border border-nd-border-visible font-mono text-caption">
      <span className="text-nd-text-primary uppercase">{connection.connection_type}</span>
      {connection.bandwidth && (
        <span className="text-nd-text-disabled">{connection.bandwidth}</span>
      )}
      {connection.latency_ms > 0 && (
        <span className="text-nd-text-disabled">{connection.latency_ms}ms</span>
      )}
      {connection.status === 'flapping' && (
        <span className="text-nd-accent font-bold uppercase">Flapping</span>
      )}
    </div>
  );
}
