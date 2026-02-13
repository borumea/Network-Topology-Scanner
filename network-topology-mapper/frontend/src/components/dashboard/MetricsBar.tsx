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
      color: '#3B82F6',
    },
    {
      icon: Link2,
      value: stats.total_connections,
      label: 'Links',
      sub: `${stats.connection_uptime_pct}% up`,
      color: '#10B981',
    },
    {
      icon: AlertTriangle,
      value: riskScore.toFixed(1),
      label: 'Risk Score',
      sub: `/10`,
      color: riskColor,
    },
    {
      icon: Shield,
      value: stats.spof_count,
      label: 'SPOFs',
      sub: `${spofs.filter((s) => s.impact > 10).length} critical`,
      color: stats.spof_count > 0 ? '#EF4444' : '#10B981',
      alert: stats.spof_count > 0,
    },
  ];

  return (
    <div className="flex gap-4 p-4 flex-shrink-0">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`
            flex-1 flex items-center gap-4 bg-bg-secondary/40 backdrop-blur-md rounded-2xl px-5 py-4 border transition-all duration-300 cursor-pointer shadow-lg group relative overflow-hidden
            ${card.alert
              ? 'border-red-500/30 bg-red-500/10 hover:border-red-500/50'
              : 'border-white/5 hover:border-white/10 hover:bg-bg-secondary/60'
            }
          `}
        >
          {/* Background Gradient Glow */}
          <div className="absolute inset-0 bg-gradient-to-br from-transparent to-white/5 opacity-0 group-hover:opacity-100 transition-opacity" />

          <div className={`
            p-3 rounded-xl bg-white/5 border border-white/5 group-hover:scale-110 transition-transform duration-300
            ${card.alert ? 'bg-red-500/20 text-red-400' : ''}
          `}>
            <card.icon size={22} style={{ color: card.alert ? undefined : card.color }} className="flex-shrink-0" />
          </div>

          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white tracking-tight">{card.value}</span>
              {card.sub && (
                <span className={`text-xs font-medium ${card.alert ? 'text-red-300' : 'text-text-muted'}`}>
                  {card.sub}
                </span>
              )}
            </div>
            <div className="text-[10px] text-text-muted/80 uppercase tracking-widest font-semibold mt-0.5">{card.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
