import { useMemo } from 'react';
import { useTopologyStore } from '../../stores/topologyStore';
import { getRiskColor } from '../../lib/graph-utils';
import { useFilterStore } from '../../stores/filterStore';

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
  const { setActiveLayer } = useFilterStore();

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

    // Calculate averages
    Object.values(groups).forEach((g) => {
      g.avgRisk = g.devices > 0 ? g.avgRisk / g.devices : 0;
    });

    return Object.values(groups).sort((a, b) => b.avgRisk - a.avgRisk);
  }, [devices, spofs]);

  const maxDevices = Math.max(...vlanGroups.map((g) => g.devices), 1);

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-xl font-bold text-text-primary mb-6">Risk Heatmap</h1>

        <div className="grid grid-cols-2 gap-4">
          {vlanGroups.map((group) => {
            const color = getRiskColor(group.avgRisk);
            const sizeRatio = group.devices / maxDevices;
            const minHeight = 120;
            const height = minHeight + sizeRatio * 100;

            return (
              <div
                key={group.vlanId}
                className="rounded-xl border border-bg-tertiary cursor-pointer hover:border-text-muted/30 transition-all relative overflow-hidden"
                style={{
                  minHeight: height,
                  backgroundColor: `${color}10`,
                  borderColor: `${color}30`,
                }}
              >
                <div className="absolute inset-0 opacity-5" style={{ backgroundColor: color }} />
                <div className="relative p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-text-primary">
                      VLAN {group.vlanId} - {group.name}
                    </h3>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-text-muted">Risk</span>
                      <span className="text-lg font-bold font-mono" style={{ color }}>
                        {group.avgRisk.toFixed(2)}
                      </span>
                    </div>

                    <div className="h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${group.avgRisk * 100}%`,
                          backgroundColor: color,
                        }}
                      />
                    </div>

                    <div className="flex justify-between text-xs">
                      <span className="text-text-secondary">{group.devices} devices</span>
                      <span className={group.spofCount > 0 ? 'text-risk-critical font-medium' : 'text-text-muted'}>
                        {group.spofCount} SPOF{group.spofCount !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {vlanGroups.length === 0 && (
          <div className="text-center text-text-muted py-12">No VLAN data available</div>
        )}
      </div>
    </div>
  );
}
