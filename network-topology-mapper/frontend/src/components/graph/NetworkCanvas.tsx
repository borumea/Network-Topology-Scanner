import { useEffect, useRef, useCallback, useState } from 'react';
import cytoscape, { Core, EventObject } from 'cytoscape';
import cola from 'cytoscape-cola';
import dagre from 'cytoscape-dagre';
import { useTopologyStore } from '../../stores/topologyStore';
import { useFilterStore } from '../../stores/filterStore';
import { cytoscapeStylesheet, getLayoutOptions } from '../../lib/cytoscape-config';
import { DEVICE_TYPE_COLORS, truncate } from '../../lib/graph-utils';
import GraphControls from './GraphControls';
import LayerToggle from './LayerToggle';
import MiniMap from './MiniMap';
import NodeTooltip from './NodeTooltip';

try { cytoscape.use(cola); } catch {}
try { cytoscape.use(dagre); } catch {}

export default function NetworkCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const tooltipRef = useRef<{ deviceId: string; x: number; y: number } | null>(null);
  const [cyReady, setCyReady] = useState(0);

  const {
    devices, connections, dependencies,
    selectedDeviceId, selectDevice,
    simulationActive, simulationResult,
    spofs,
  } = useTopologyStore();

  const { activeLayout, showLabels, showRiskHalos, deviceTypeFilter, statusFilter } = useFilterStore();

  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      style: cytoscapeStylesheet,
      layout: { name: 'preset' },
      minZoom: 0.1,
      maxZoom: 4,
      wheelSensitivity: 0.3,
    });

    cy.on('tap', 'node', (evt: EventObject) => selectDevice(evt.target.id()));
    cy.on('tap', (evt: EventObject) => { if (evt.target === cy) selectDevice(null); });

    cy.on('mouseover', 'node', (evt: EventObject) => {
      const node = evt.target;
      const pos = node.renderedPosition();
      tooltipRef.current = { deviceId: node.id(), x: pos.x, y: pos.y };
      containerRef.current?.dispatchEvent(new CustomEvent('node-hover', { detail: tooltipRef.current }));
      const neighborhood = node.closedNeighborhood();
      cy.elements().addClass('dimmed');
      neighborhood.removeClass('dimmed').addClass('highlighted');
    });

    cy.on('mouseout', 'node', () => {
      tooltipRef.current = null;
      containerRef.current?.dispatchEvent(new CustomEvent('node-hover', { detail: null }));
      cy.elements().removeClass('dimmed highlighted');
    });

    cy.on('mouseover', 'edge', (evt: EventObject) => {
      const edge = evt.target;
      edge.addClass('edge-hovered');
      const midpoint = edge.midpoint();
      const z = cy.zoom();
      const pan = cy.pan();
      containerRef.current?.dispatchEvent(new CustomEvent('edge-hover', {
        detail: {
          x: midpoint.x * z + pan.x,
          y: midpoint.y * z + pan.y,
          connection_type: edge.data('connection_type') || 'unknown',
          bandwidth: edge.data('bandwidth') || 'N/A',
          latency: edge.data('latency_ms'),
          status: edge.data('status') || 'active',
          is_redundant: edge.data('is_redundant') || false,
        },
      }));
    });

    cy.on('mouseout', 'edge', () => {
      cy.edges().removeClass('edge-hovered');
      containerRef.current?.dispatchEvent(new CustomEvent('edge-hover', { detail: null }));
    });

    cy.on('dbltap', 'node', (evt: EventObject) => {
      const neighborhood = evt.target.closedNeighborhood();
      cy.animate({ fit: { eles: neighborhood, padding: 80 }, duration: 400, easing: 'ease-in-out-cubic' } as any);
    });

    cyRef.current = cy;
    setCyReady((c) => c + 1);
    return () => { cy.destroy(); cyRef.current = null; };
  }, [selectDevice]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.batch(() => {
      cy.elements().remove();

      let filteredDevices = devices;
      if (deviceTypeFilter.length > 0) filteredDevices = filteredDevices.filter((d) => deviceTypeFilter.includes(d.device_type));
      if (statusFilter.length > 0) filteredDevices = filteredDevices.filter((d) => statusFilter.includes(d.status));

      const deviceIds = new Set(filteredDevices.map((d) => d.id));
      const spofIds = new Set(spofs.map((s) => s.device_id));

      filteredDevices.forEach((device) => {
        cy.add({
          group: 'nodes',
          data: {
            id: device.id, label: showLabels ? truncate(device.hostname || device.ip) : '',
            device_type: device.device_type, status: device.status,
            is_gateway: device.is_gateway || undefined,
            highRisk: device.risk_score > 0.6 && showRiskHalos ? true : undefined,
            risk_score: device.risk_score, ip: device.ip, hostname: device.hostname,
            vendor: device.vendor, isSPOF: spofIds.has(device.id) || undefined,
          },
        });
      });

      connections.forEach((conn) => {
        if (deviceIds.has(conn.source_id) && deviceIds.has(conn.target_id)) {
          cy.add({
            group: 'edges',
            data: {
              id: conn.id, source: conn.source_id, target: conn.target_id,
              connection_type: conn.connection_type, bandwidth: conn.bandwidth,
              latency_ms: conn.latency_ms, status: conn.status,
              is_redundant: conn.is_redundant || undefined,
            },
          });
        }
      });

      dependencies.forEach((dep) => {
        if (deviceIds.has(dep.source_id) && deviceIds.has(dep.target_id)) {
          cy.add({
            group: 'edges',
            data: {
              id: `dep-${dep.id}`, source: dep.source_id, target: dep.target_id,
              isDependency: true, dependency_type: dep.dependency_type,
            },
          });
        }
      });
    });

    cy.layout(getLayoutOptions(activeLayout)).run();
    setCyReady((c) => c + 1);
  }, [devices, connections, dependencies, activeLayout, showLabels, showRiskHalos, deviceTypeFilter, statusFilter, spofs]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.nodes().unselect();
    if (selectedDeviceId) cy.getElementById(selectedDeviceId).select();
  }, [selectedDeviceId]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.nodes().removeClass('sim-removed sim-disconnected sim-degraded sim-safe');
    if (simulationActive && simulationResult) {
      const { removed_node_ids, disconnected_devices, degraded_devices, safe_device_ids } = simulationResult;
      removed_node_ids.forEach((id) => cy.getElementById(id).addClass('sim-removed'));
      disconnected_devices.forEach((d) => cy.getElementById(d.id).addClass('sim-disconnected'));
      degraded_devices.forEach((d) => cy.getElementById(d.id).addClass('sim-degraded'));
      safe_device_ids.forEach((id) => cy.getElementById(id).addClass('sim-safe'));
    }
  }, [simulationActive, simulationResult]);

  const handleFit = useCallback(() => cyRef.current?.fit(undefined, 50), []);
  const handleZoomIn = useCallback(() => { const cy = cyRef.current; if (cy) cy.zoom(cy.zoom() * 1.3); }, []);
  const handleZoomOut = useCallback(() => { const cy = cyRef.current; if (cy) cy.zoom(cy.zoom() / 1.3); }, []);

  return (
    <div className="relative w-full h-full">
      <LayerToggle />
      <div ref={containerRef} className="w-full h-full bg-bg-primary" />
      <MiniMap cy={cyRef.current} key={cyReady} />
      <GraphControls onFit={handleFit} onZoomIn={handleZoomIn} onZoomOut={handleZoomOut} />
      <NodeTooltip containerRef={containerRef} devices={devices} />
    </div>
  );
}
