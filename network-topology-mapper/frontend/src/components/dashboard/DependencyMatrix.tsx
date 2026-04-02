import { useMemo } from 'react';
import { useTopologyStore } from '../../stores/topologyStore';
import DeviceIcon from '../shared/DeviceIcon';
import type { DeviceType } from '../../types/topology';

export default function DependencyMatrix() {
  const { devices, dependencies } = useTopologyStore();

  const { servers, matrix } = useMemo(() => {
    const srvDevices = devices.filter((d) =>
      ['server', 'firewall', 'router'].includes(d.device_type)
    );

    const depMap = new Map<string, Set<string>>();
    dependencies.forEach((dep) => {
      if (!depMap.has(dep.source_id)) depMap.set(dep.source_id, new Set());
      depMap.get(dep.source_id)!.add(dep.target_id);
    });

    return { servers: srvDevices, matrix: depMap };
  }, [devices, dependencies]);

  if (servers.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <span className="font-mono text-caption text-nd-text-disabled">[NO DEPENDENCY DATA]</span>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="font-display text-display-md font-bold text-black mb-6">Dependencies</h1>

        <div className="overflow-x-auto">
          <table className="border-collapse">
            <thead>
              <tr>
                <th className="p-2 font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled text-left sticky left-0 bg-nd-black z-10">
                  Depends on {'\u2192'}
                </th>
                {servers.slice(0, 20).map((s) => (
                  <th key={s.id} className="p-2">
                    <div className="flex flex-col items-center gap-1 min-w-[60px]">
                      <DeviceIcon type={s.device_type as DeviceType} size={12} />
                      <span className="font-mono text-label text-nd-text-disabled truncate max-w-[60px]">
                        {s.hostname.split('-').pop() || s.ip.split('.').pop()}
                      </span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {servers.slice(0, 20).map((row) => (
                <tr key={row.id}>
                  <td className="p-2 font-mono text-caption text-nd-text-secondary sticky left-0 bg-nd-black z-10 border-r border-nd-border">
                    <div className="flex items-center gap-2">
                      <DeviceIcon type={row.device_type as DeviceType} size={12} />
                      <span className="truncate max-w-[100px]">{row.hostname || row.ip}</span>
                    </div>
                  </td>
                  {servers.slice(0, 20).map((col) => {
                    const hasDep = matrix.get(row.id)?.has(col.id);
                    const isSelf = row.id === col.id;

                    return (
                      <td key={col.id} className="p-2 text-center">
                        {isSelf ? (
                          <div className="w-4 h-4 bg-nd-border mx-auto" />
                        ) : hasDep ? (
                          <div className="w-4 h-4 bg-black mx-auto" title={`${row.hostname} depends on ${col.hostname}`} />
                        ) : (
                          <div className="w-4 h-4 bg-nd-surface-raised mx-auto" />
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center gap-4 mt-4">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 bg-black" />
            <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">Dependency</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 bg-nd-surface-raised" />
            <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">None</span>
          </div>
        </div>
      </div>
    </div>
  );
}
