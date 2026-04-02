import { useMemo } from 'react';
import { useTopologyStore } from '../../stores/topologyStore';
import { getRiskColor } from '../../lib/graph-utils';

interface VlanGroup {
  vlanId: number;
  name: string;
  devices: number;
  avgRisk: number;
  spofCount: number;
}

const VLAN_NAMES: Record<number, string> = {
  10: 'Engineering',
  20: 'Corporate',
  30: 'DMZ',
  40: 'Management',
  50: 'IoT',
};

export default function RiskHeatmap() {
  const { devices, spofs } = useTopologyStore();

  const vlanGroups = useMemo(() => {
    const groups: Record<number, VlanGroup> = {};
    const spofDeviceIds = new Set(spofs.map((s) => s.device_id));

    devices.forEach((d) => {
      d.vlan_ids.forEach((vlan) => {
        if (!groups[vlan]) {
          groups[vlan] = {
            vlanId: vlan,
            name: VLAN_NAMES[vlan] || `VLAN ${vlan}`,
            devices: 0,
            avgRisk: 0,
            spofCount: 0,
          };
        }
        groups[vlan].devices++;
        groups[vlan].avgRisk += d.risk_score;
        if (spofDeviceIds.has(d.id)) {
          groups[vlan].spofCount++;
        }
      });
    });

    Object.values(groups).forEach((g) => {
      g.avgRisk = g.devices > 0 ? g.avgRisk / g.devices : 0;
    });

    return Object.values(groups).sort((a, b) => b.avgRisk - a.avgRisk);
  }, [devices, spofs]);

  const segments = 10;

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="font-display text-display-md font-bold text-black mb-6">Risk Heatmap</h1>

        <div className="grid grid-cols-2 gap-4">
          {vlanGroups.map((group) => {
            const color = getRiskColor(group.avgRisk);
            const filled = Math.round(group.avgRisk * segments);

            return (
              <div
                key={group.vlanId}
                className="bg-nd-surface rounded-nd-card border border-nd-border p-5 hover:border-nd-border-visible transition-colors"
              >
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-sans text-body-sm font-medium text-nd-text-display">
                      {group.name}
                    </h3>
                    <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">VLAN {group.vlanId}</span>
                  </div>
                  <span className="font-mono text-heading font-bold" style={{ color }}>
                    {group.avgRisk.toFixed(2)}
                  </span>
                </div>

                {/* Segmented bar */}
                <div className="h-2 flex gap-[2px] mb-3">
                  {Array.from({ length: segments }).map((_, i) => (
                    <div
                      key={i}
                      className="flex-1 h-full"
                      style={{ backgroundColor: i < filled ? color : '#E8E8E8' }}
                    />
                  ))}
                </div>

                <div className="flex justify-between">
                  <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">{group.devices} devices</span>
                  <span className={`font-mono text-label uppercase tracking-[0.08em] ${group.spofCount > 0 ? 'text-nd-accent font-bold' : 'text-nd-text-disabled'}`}>
                    {group.spofCount} SPOF{group.spofCount !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {vlanGroups.length === 0 && (
          <div className="text-center py-12 font-mono text-caption text-nd-text-disabled">[NO VLAN DATA AVAILABLE]</div>
        )}
      </div>
    </div>
  );
}
