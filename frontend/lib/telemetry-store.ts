import { useSyncExternalStore } from "react";

import type { BrewSessionSummary, TelemetryPacket, TelemetryPoint } from "./types";

type StoreState = {
  connected: boolean;
  lastMessageAt: number | null;
  latestTelemetry: TelemetryPoint | null;
  session: BrewSessionSummary | null;
  rawFlowRate: number;
  smoothedFlowRate: number;
  flowWindow: Array<{ ts: number; value: number }>;
  error: string | null;
};

const WINDOW_MS = 1250;

const listeners = new Set<() => void>();
let state: StoreState = {
  connected: false,
  lastMessageAt: null,
  latestTelemetry: null,
  session: null,
  rawFlowRate: 0,
  smoothedFlowRate: 0,
  flowWindow: [],
  error: null,
};

function emit() {
  for (const listener of listeners) listener();
}

export function getTelemetryState() {
  return state;
}

export function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function setConnected(connected: boolean) {
  state = { ...state, connected };
  emit();
}

export function ingestPacket(packet: TelemetryPacket) {
  const now = Date.now();
  if (packet.type === "telemetry" && packet.telemetry) {
    const rawFlowRate = packet.telemetry.raw_flow_rate ?? 0;
    const nextWindow = [...state.flowWindow, { ts: now, value: rawFlowRate }].filter((entry) => now - entry.ts <= WINDOW_MS);
    const smoothedFlowRate = nextWindow.length ? nextWindow.reduce((sum, entry) => sum + entry.value, 0) / nextWindow.length : rawFlowRate;
    state = {
      ...state,
      lastMessageAt: now,
      latestTelemetry: packet.telemetry,
      session: packet.session ?? state.session,
      rawFlowRate,
      smoothedFlowRate,
      flowWindow: nextWindow,
      error: null,
    };
    emit();
    return;
  }

  if (packet.type === "session" && packet.session) {
    state = { ...state, session: packet.session, lastMessageAt: now };
    emit();
    return;
  }

  if (packet.type === "error") {
    state = { ...state, error: packet.message ?? "unknown error" };
    emit();
  }
}

export function useTelemetrySelector<T>(selector: (state: StoreState) => T): T {
  return useSyncExternalStore(subscribe, () => selector(getTelemetryState()), () => selector(getTelemetryState()));
}

export function resetClientTelemetryState() {
  state = {
    connected: false,
    lastMessageAt: null,
    latestTelemetry: null,
    session: null,
    rawFlowRate: 0,
    smoothedFlowRate: 0,
    flowWindow: [],
    error: null,
  };
  emit();
}
