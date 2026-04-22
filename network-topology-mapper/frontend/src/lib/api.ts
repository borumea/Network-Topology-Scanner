const API_BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// Topology
export const fetchTopology = (params?: Record<string, string>) => {
  const query = params ? '?' + new URLSearchParams(params).toString() : '';
  return request<any>(`/topology${query}`);
};

export const fetchTopologyStats = () => request<any>('/topology/stats');

export const clearTopology = () =>
  request<any>('/topology', { method: 'DELETE' });

export const fetchDevice = (id: string) => request<any>(`/devices/${id}`);

export const fetchDeviceConnections = (id: string) =>
  request<any>(`/devices/${id}/connections`);

export const fetchDeviceDependencies = (id: string) =>
  request<any>(`/devices/${id}/dependencies`);

// Scans
export const triggerScan = (type: string = 'full', target: string = '192.168.0.0/16', intensity: string = 'normal') =>
  request<any>('/scans', {
    method: 'POST',
    body: JSON.stringify({ type, target, intensity }),
  });

export const fetchScans = () => request<any>('/scans');

export const fetchScan = (id: string) => request<any>(`/scans/${id}`);

export const cancelScan = (id: string) =>
  request<any>(`/scans/${id}`, { method: 'DELETE' });

// Simulation
export const simulateFailure = (removeNodes: string[], removeEdges: string[][] = []) =>
  request<any>('/simulate/failure', {
    method: 'POST',
    body: JSON.stringify({ remove_nodes: removeNodes, remove_edges: removeEdges }),
  });

export const fetchSPOFs = () => request<any>('/simulate/spof');

export const fetchResilience = () => request<any>('/simulate/resilience');

// Alerts
export const fetchAlerts = (params?: Record<string, string>) => {
  const query = params ? '?' + new URLSearchParams(params).toString() : '';
  return request<any>(`/alerts${query}`);
};

export const updateAlert = (id: string, status: string) =>
  request<any>(`/alerts/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });

// Reports
export const fetchResilienceReport = () => request<any>('/reports/resilience');

export const fetchChangelog = (from?: string, to?: string) => {
  const params: Record<string, string> = {};
  if (from) params.from = from;
  if (to) params.to = to;
  return request<any>(`/reports/changelog?${new URLSearchParams(params)}`);
};

// Settings
export const fetchSettings = () => request<any>('/settings');

// Health
export const fetchHealth = () => request<any>('/health');
