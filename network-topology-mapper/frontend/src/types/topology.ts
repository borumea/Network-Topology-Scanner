export type DeviceType =
  | 'router'
  | 'switch'
  | 'server'
  | 'workstation'
  | 'firewall'
  | 'ap'
  | 'printer'
  | 'iot'
  | 'unknown';

export type DeviceStatus = 'online' | 'offline' | 'degraded';

export type ConnectionType = 'ethernet' | 'fiber' | 'wireless' | 'vpn' | 'virtual';

export type ConnectionStatus = 'active' | 'disabled' | 'degraded' | 'flapping';

export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export type AlertType =
  | 'new_device'
  | 'topology_change'
  | 'spof'
  | 'anomaly'
  | 'flapping'
  | 'device_offline'
  | 'config_drift';

export type AlertStatus = 'open' | 'acknowledged' | 'resolved' | 'dismissed';

export type ScanType = 'active' | 'passive' | 'snmp' | 'full';

export type ScanStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export type LayerType = 'physical' | 'logical' | 'application';

export type LayoutType = 'cola' | 'dagre' | 'circle' | 'grid';

export interface Device {
  id: string;
  ip: string;
  mac: string;
  hostname: string;
  device_type: DeviceType;
  vendor: string;
  model: string;
  os: string;
  open_ports: number[];
  services: string[];
  first_seen: string;
  last_seen: string;
  discovery_method: string;
  vlan_ids: number[];
  subnet: string;
  location: string;
  risk_score: number;
  criticality: 'high' | 'medium' | 'low';
  is_gateway: boolean;
  status: DeviceStatus;
  tier: number;
  risk_details?: RiskDetails;
}

export interface RiskDetails {
  device_id: string;
  risk_score: number;
  factors: string[];
}

export interface Connection {
  id: string;
  source_id: string;
  target_id: string;
  connection_type: ConnectionType;
  bandwidth: string;
  switch_port: string;
  vlan: number | null;
  latency_ms: number;
  packet_loss_pct: number;
  is_redundant: boolean;
  protocol: string;
  status: ConnectionStatus;
  first_seen: string;
  last_seen: string;
}

export interface Dependency {
  id: string;
  source_id: string;
  target_id: string;
  dependency_type: string;
  service_port: number;
  criticality: string;
  discovered_via: string;
}

export interface Topology {
  devices: Device[];
  connections: Connection[];
  dependencies: Dependency[];
}

export interface TopologyStats {
  total_devices: number;
  total_connections: number;
  online: number;
  offline: number;
  degraded: number;
  active_connections: number;
  connection_uptime_pct: number;
  type_counts: Record<string, number>;
  risk_score: number;
  spof_count: number;
  avg_device_risk: number;
}

export interface Alert {
  id: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  title: string;
  description: string;
  device_id: string | null;
  details: Record<string, any>;
  created_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  status: AlertStatus;
}

export interface Scan {
  id: string;
  scan_type: ScanType;
  status: ScanStatus;
  started_at: string | null;
  completed_at: string | null;
  target_range: string;
  devices_found: number;
  new_devices: number;
  config: Record<string, any>;
  progress?: ScanProgress;
}

export interface ScanProgress {
  scan_id: string;
  percent: number;
  phase: string;
  devices_found: number;
  log_messages?: string[];
}

export interface SPOF {
  device_id: string;
  hostname: string;
  device_type: string;
  impact: number;
  reason: string;
  risk_score: number;
}

export interface SimulationResult {
  blast_radius: number;
  blast_radius_pct: number;
  disconnected_devices: SimulatedDevice[];
  degraded_devices: SimulatedDevice[];
  safe_device_ids: string[];
  removed_node_ids: string[];
  affected_services: string[];
  risk_delta: number;
  new_components: number;
  recommendations: Recommendation[];
}

export interface SimulatedDevice {
  id: string;
  hostname: string;
  device_type: string;
  status: string;
  lost_connections?: number;
}

export interface Recommendation {
  action: string;
  impact: string;
  priority: string;
}

export interface ResilienceReport {
  generated: boolean;
  score: number;
  max_score: number;
  report: string;
  spofs: SPOF[];
  stats: { total_devices: number; total_connections: number };
}

export interface ResilienceScore {
  score: number;
  max_score: number;
  breakdown: {
    connectivity: number;
    redundancy: number;
    spof_resistance: number;
    path_diversity: number;
  };
  total_devices: number;
  total_connections: number;
  spof_count: number;
  spofs: SPOF[];
}

export interface TopologySnapshot {
  id: string;
  created_at: string;
  device_count: number;
  connection_count: number;
  risk_score: number;
  snapshot_data: Record<string, any>;
}

export interface WSMessage {
  type: string;
  data: any;
}

export type ViewType =
  | 'topology'
  | 'dashboard'
  | 'scan'
  | 'simulate'
  | 'alerts'
  | 'heatmap'
  | 'timeline'
  | 'reports'
  | 'settings';
