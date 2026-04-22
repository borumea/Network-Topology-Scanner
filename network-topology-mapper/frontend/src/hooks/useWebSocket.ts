import { useEffect, useRef, useCallback, useState } from 'react';
import { useTopologyStore } from '../stores/topologyStore';
import type { WSMessage, Device, Connection } from '../types/topology';

const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL = `${WS_PROTOCOL}//${window.location.host}/ws/topology`;
const RECONNECT_INTERVAL = 3000;
const HEARTBEAT_INTERVAL = 30000;

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<number>();
  const reconnectRef = useRef<number>();
  const [connected, setConnected] = useState(false);

  const { addDevice, updateDevice, removeDevice, updateConnection, clearTopology } = useTopologyStore();

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);

        switch (msg.type) {
          case 'device_added':
            addDevice(msg.data as Device);
            break;
          case 'device_update':
            updateDevice(msg.data as Device);
            break;
          case 'device_removed':
            removeDevice(msg.data.id);
            break;
          case 'connection_change':
            updateConnection(msg.data as Connection);
            break;
          case 'topology_cleared':
            clearTopology();
            break;
          case 'alert':
            // Alerts handled by useAlerts hook
            window.dispatchEvent(new CustomEvent('ws-alert', { detail: msg.data }));
            break;
          case 'scan_progress':
            window.dispatchEvent(new CustomEvent('ws-scan-progress', { detail: msg.data }));
            break;
          case 'pong':
            break;
        }
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    },
    [addDevice, updateDevice, removeDevice, updateConnection, clearTopology]
  );

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        setConnected(true);
        ws.send(JSON.stringify({ type: 'subscribe', channel: 'topology' }));

        heartbeatRef.current = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, HEARTBEAT_INTERVAL);
      };

      ws.onmessage = handleMessage;

      ws.onclose = () => {
        setConnected(false);
        if (heartbeatRef.current) clearInterval(heartbeatRef.current);
        reconnectRef.current = window.setTimeout(connect, RECONNECT_INTERVAL);
      };

      ws.onerror = () => {
        setConnected(false);
        ws.close();
      };

      wsRef.current = ws;
    } catch {
      reconnectRef.current = window.setTimeout(connect, RECONNECT_INTERVAL);
    }
  }, [handleMessage]);

  useEffect(() => {
    connect();
    return () => {
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected };
}
