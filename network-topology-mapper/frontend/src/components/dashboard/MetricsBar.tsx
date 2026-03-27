import { Radio, Link2, AlertTriangle, Shield } from 'lucide-react';
import { useTopologyStore } from '../../stores/topologyStore';
import { getRiskColor } from '../../lib/graph-utils';

export default function MetricsBar() {
  const { stats, spofs } = useTopologyStore();

  if (!stats) return null;

  const riskScore = stats.risk_score;
  const riskColor = getRiskColor(riskScore / 10);

  const cards = [
    {
      icon: Radio,
      value: stats.total_devices,
      label: 'Devices',
      sub: `${stats.online} online`,
      color: '#6366F1',
    },
    {
      icon: Link2,
      value: stats.total_connections,
      label: 'Links',
      sub: `${stats.connection_uptime_pct}% uptime`,
      color: '#34D399',
    },
    {
      icon: AlertTriangle,
      value: riskScore.toFixed(1),
      label: 'Risk Score',
      sub: '/ 10',
      color: riskColor,
    },
    {
      icon: Shield,
      value: stats.spof_count,
      label: 'SPOFs',
      sub: `${spofs.filter((s) => s.impact > 10).length} critical`,
      color: stats.spof_count > 0 ? '#F87171' : '#34D399',
      alert: stats.spof_count > 0,
    },
  ];

  return (
    <div className="flex gap-3 px-4 py-3 border-b border-border flex-shrink-0">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`flex-1 flex items-center gap-3 rounded-lg px-3.5 py-2.5 border transition-colors ${
            card.alert
              ? 'border-status-offline/20 bg-status-offline/5'
              : 'border-border bg-bg-secondary'
          }`}
        >
          <card.icon size={16} style={{ color: card.color }} className="flex-shrink-0 opacity-70" />
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-lg font-semibold text-text-primary leading-none">{card.value}</span>
              <span className="text-[11px] text-text-muted">{card.sub}</span>
            </div>
            <div className="text-[11px] text-text-muted mt-0.5">{card.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
