import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * WebSocket Hook for Real-Time Dashboard Updates
 * Connects to backend WebSocket for live data streaming
 */
export function useWebSocket(url, options = {}) {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectInterval = 3000,
    reconnectAttempts = 5,
    heartbeatInterval = 30000
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef(null);
  const heartbeatIntervalRef = useRef(null);

  // Send message through WebSocket
  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    console.warn('WebSocket not connected');
    return false;
  }, []);

  // Setup heartbeat to keep connection alive
  const setupHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }

    heartbeatIntervalRef.current = setInterval(() => {
      sendMessage({ type: 'ping' });
    }, heartbeatInterval);
  }, [heartbeatInterval, sendMessage]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    try {
      const token = localStorage.getItem('token');
      const wsUrl = url.includes('?')
        ? `${url}&token=${token}`
        : `${url}?token=${token}`;

      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectCountRef.current = 0;
        setupHeartbeat();
        onConnect?.();
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          onMessage?.(data);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('Connection error');
        onError?.(event);
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        onDisconnect?.();

        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }

        // Attempt reconnection
        if (reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current += 1;
          console.log(`Reconnecting... Attempt ${reconnectCountRef.current}`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else {
          setError('Max reconnection attempts reached');
        }
      };
    } catch (err) {
      console.error('Failed to connect WebSocket:', err);
      setError(err.message);
    }
  }, [url, onMessage, onConnect, onDisconnect, onError, reconnectInterval, reconnectAttempts, setupHeartbeat]);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Connect on mount
  useEffect(() => {
    if (url) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [url]);

  return {
    isConnected,
    lastMessage,
    error,
    sendMessage,
    disconnect,
    reconnect: connect
  };
}

/**
 * Hook for Dashboard Real-Time Updates
 */
export function useDashboardWebSocket() {
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
  const WS_BASE_URL = API_BASE_URL.replace('http', 'ws').replace('/api', '');
  const wsUrl = `${WS_BASE_URL}/ws/dashboard/`;

  const [updates, setUpdates] = useState({
    contracts: null,
    risks: null,
    profitability: null,
    timestamp: null
  });

  const handleMessage = useCallback((data) => {
    console.log('Dashboard update received:', data);

    switch (data.type) {
      case 'contract_update':
        setUpdates(prev => ({
          ...prev,
          contracts: data.payload,
          timestamp: new Date().toISOString()
        }));
        break;

      case 'risk_update':
        setUpdates(prev => ({
          ...prev,
          risks: data.payload,
          timestamp: new Date().toISOString()
        }));
        break;

      case 'profitability_update':
        setUpdates(prev => ({
          ...prev,
          profitability: data.payload,
          timestamp: new Date().toISOString()
        }));
        break;

      case 'full_refresh':
        setUpdates({
          contracts: data.payload.contracts,
          risks: data.payload.risks,
          profitability: data.payload.profitability,
          timestamp: new Date().toISOString()
        });
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  }, []);

  const websocket = useWebSocket(wsUrl, {
    onMessage: handleMessage,
    onConnect: () => {
      console.log('Dashboard WebSocket connected');
    },
    onDisconnect: () => {
      console.log('Dashboard WebSocket disconnected');
    },
    reconnectInterval: 5000,
    reconnectAttempts: 10
  });

  return {
    ...websocket,
    updates,
    requestRefresh: () => {
      websocket.sendMessage({ type: 'request_refresh' });
    }
  };
}

export default useWebSocket;
