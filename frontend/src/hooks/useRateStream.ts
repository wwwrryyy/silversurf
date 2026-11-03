import { useEffect, useRef, useState, useCallback } from 'react';
import { SSEConnectionState, SSERateEvent } from '../types';

interface UseRateStreamOptions {
  url?: string;
  onEvent?: (event: SSERateEvent) => void;
  enabled?: boolean;
}

export function useRateStream({
  url = '/v1/silver/stream',
  onEvent,
  enabled = true,
}: UseRateStreamOptions = {}) {
  const [connectionState, setConnectionState] = useState<SSEConnectionState>('disconnected');
  const [lastEvent, setLastEvent] = useState<SSERateEvent | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const retryDelayRef = useRef<number>(1000); // Start at 1s
  const eventSourceRef = useRef<EventSource | null>(null);
  const onEventRef = useRef(onEvent);

  // Keep latest onEvent callback ref
  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  const connect = useCallback(() => {
    if (!enabled) return;

    // Clean up any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    setConnectionState('connecting');

    try {
      const es = new EventSource(url);
      eventSourceRef.current = es;

      es.onopen = () => {
        setConnectionState('connected');
        retryDelayRef.current = 1000; // Reset backoff on successful connect
      };

      const handleRateMessage = (eventType: 'rate.published' | 'rate.revised') => (event: MessageEvent) => {
        try {
          const parsedData = JSON.parse(event.data);
          const sseEvent: SSERateEvent = {
            event: eventType,
            data: parsedData,
          };
          setLastEvent(sseEvent);
          onEventRef.current?.(sseEvent);
        } catch (err) {
          console.error(`Failed to parse SSE payload for ${eventType}:`, err);
        }
      };

      es.addEventListener('rate.published', handleRateMessage('rate.published'));
      es.addEventListener('rate.revised', handleRateMessage('rate.revised'));

      es.addEventListener('ping', () => {
        // Keepalive received; confirms active link
        setConnectionState('connected');
      });

      es.onerror = () => {
        setConnectionState('disconnected');
        es.close();
        eventSourceRef.current = null;

        if (enabled) {
          // Schedule reconnect with exponential backoff (capped at 30s)
          const nextDelay = Math.min(retryDelayRef.current, 30000);
          retryDelayRef.current = Math.min(nextDelay * 2, 30000);

          if (reconnectTimeoutRef.current) {
            window.clearTimeout(reconnectTimeoutRef.current);
          }

          reconnectTimeoutRef.current = window.setTimeout(() => {
            connect();
          }, nextDelay);
        }
      };
    } catch (err) {
      console.error('Failed to initialize EventSource:', err);
      setConnectionState('disconnected');
    }
  }, [url, enabled]);

  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      setConnectionState('disconnected');
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        window.clearTimeout(reconnectTimeoutRef.current);
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [connect, enabled]);

  const reconnect = useCallback(() => {
    retryDelayRef.current = 1000;
    connect();
  }, [connect]);

  return {
    connectionState,
    lastEvent,
    reconnect,
  };
}
