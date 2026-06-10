import type { Bean, BrewLog } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export async function listBeans(): Promise<Bean[]> {
  return request<Bean[]>("/api/beans");
}

export async function getBean(beanId: number): Promise<Bean> {
  return request<Bean>(`/api/beans/${beanId}`);
}

export async function createBean(payload: Omit<Bean, "id" | "is_archived" | "days_from_roast">): Promise<Bean> {
  return request<Bean>("/api/beans", { method: "POST", body: JSON.stringify(payload) });
}

export async function archiveBean(beanId: number, isArchived: boolean): Promise<void> {
  await request(`/api/beans/${beanId}`, { method: "PATCH", body: JSON.stringify({ is_archived: isArchived }) });
}

export async function listBrewLogs(filters?: { beanId?: number; beanName?: string; rating?: number }): Promise<BrewLog[]> {
  const params = new URLSearchParams();
  if (filters?.beanId) params.set("bean_id", String(filters.beanId));
  if (filters?.beanName) params.set("bean_name", filters.beanName);
  if (filters?.rating) params.set("rating", String(filters.rating));
  return request<BrewLog[]>(`/api/brew-logs${params.toString() ? `?${params.toString()}` : ""}`);
}

export async function getBrewLog(logId: number): Promise<BrewLog> {
  return request<BrewLog>(`/api/brew-logs/${logId}`);
}

export async function saveBrewLog(payload: Record<string, unknown>): Promise<BrewLog> {
  return request<BrewLog>("/api/brew-logs", { method: "POST", body: JSON.stringify(payload) });
}

export function getWsUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
  const url = new URL(base);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = "/ws/telemetry";
  url.search = "";
  return url.toString();
}
