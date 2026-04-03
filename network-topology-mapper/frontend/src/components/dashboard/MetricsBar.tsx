import { useTopologyStore } from '../../stores/topologyStore';

export default function MetricsBar() {
  const { stats, spofs } = useTopologyStore();

  if (!stats) return null;

  const riskScore = stats.risk_score;
  const riskColor = riskScore < 3 ? '#4A9E5C' : riskScore < 6 ? '#D4A843' : '#D71921';
  const spofColor = stats.spof_count > 0 ? '#D71921' : '#4A9E5C';

  const cards = [
    {
      value: stats.total_devices,
      label: 'Devices',
      sub: `${stats.online} online`,
      color: '#1A1A1A',
    },
    {
      value: stats.total_connections,
      label: 'Links',
      sub: `${stats.connection_uptime_pct}% uptime`,
      color: '#1A1A1A',
    },
    {
      value: riskScore.toFixed(1),
      label: 'Risk Score',
      sub: '/ 10',
      color: riskColor,
    },
    {
      value: stats.spof_count,
      label: 'SPOFs',
      sub: `${spofs.filter((s) => s.impact > 10).length} critical`,
      color: spofColor,
    },
  ];

  return (
    <div className="flex gap-3 px-4 py-3 border-b border-nd-border flex-shrink-0">
      {cards.map((card) => (
        <div
          key={card.label}
          className="flex-1 flex items-center gap-3 rounded-nd-compact px-4 py-3 border border-nd-border bg-nd-surface"
        >
          <div>
            <div className="flex items-baseline gap-1.5">
              <span
                className="font-mono text-[24px] font-bold leading-none"
                style={{ color: card.color }}
              >
                {card.value}
              </span>
              <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">
                {card.sub}
              </span>
            </div>
            <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary mt-1">
              {card.label}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
