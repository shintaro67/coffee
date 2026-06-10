"use client";

import { useEffect, useMemo, useRef } from "react";

import { getWsUrl } from "@/lib/api";
import { ingestPacket, setConnected } from "@/lib/telemetry-store";
import type { TelemetryPacket } from "@/lib/types";

export type TelemetrySocketApi = {
  sendCommand: (command: "tare" | "start") => void;
};

export function useTelemetrySocket(): TelemetrySocketApi {
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let cancelled = false;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let socket: WebSocket | null = null;

    const connect = () => {
      socket = new WebSocket(getWsUrl());
      wsRef.current = socket;

      socket.onopen = () => {
        if (cancelled) {
          socket?.close();
          return;
        }
        setConnected(true);
      };
      socket.onclose = () => {
        setConnected(false);
        if (!cancelled) {
          retryTimer = setTimeout(connect, 1000);
        }
      };
      socket.onerror = () => setConnected(false);
      socket.onmessage = (event) => {
        try {
          const packet = JSON.parse(event.data) as TelemetryPacket;
          ingestPacket(packet);
        } catch {
          ingestPacket({ type: "error", message: "invalid websocket payload" });
        }
      };
    };

    connect();

    return () => {
      cancelled = true;
      if (retryTimer) clearTimeout(retryTimer);
      if (socket?.readyState === WebSocket.OPEN) {
        socket.close();
      }
      wsRef.current = null;
    };
  }, []);

  return useMemo(
    () => ({
      sendCommand: (command: "tare" | "start") => {
        const socket = wsRef.current;
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(command);
        }
      },
    }),
    [],
  );
}
