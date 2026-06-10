"use client";

import { useEffect, useMemo, useState } from "react";

import { getBrewLog, listBeans, listBrewLogs } from "@/lib/api";
import type { Bean, BrewLog } from "@/lib/types";
import { Area, AreaChart, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Filters = {
  beanName: string;
  rating: string;
};

export function HistoryView() {
  const [beans, setBeans] = useState<Bean[]>([]);
  const [logs, setLogs] = useState<BrewLog[]>([]);
  const [selected, setSelected] = useState<BrewLog | null>(null);
  const [filters, setFilters] = useState<Filters>({ beanName: "", rating: "" });

  const load = async () => {
    const data = await listBrewLogs({ beanName: filters.beanName || undefined, rating: filters.rating ? Number(filters.rating) : undefined });
    setLogs(data);
  };

  useEffect(() => {
    listBeans().then(setBeans).catch(() => undefined);
    load().catch(() => undefined);
  }, []);

  useEffect(() => {
    load().catch(() => undefined);
  }, [filters.beanName, filters.rating]);

  const chartData = useMemo(() => selected?.timeseries_json ?? [], [selected]);
  const summary = useMemo(() => {
    if (!selected || chartData.length === 0) return null;
    const peakWeight = Math.max(...chartData.map((entry) => entry.weight));
    const maxFlow = Math.max(...chartData.map((entry) => entry.flow_rate));
    const avgFlow = chartData.reduce((sum, entry) => sum + entry.flow_rate, 0) / chartData.length;
    return { peakWeight, maxFlow, avgFlow };
  }, [chartData, selected]);

  return (
    <div className="space-y-6">
      <div className="glass-panel rounded-3xl p-5">
        <div className="grid gap-3 md:grid-cols-3">
          <label className="block">
            <span className="mb-1 block text-sm text-slate-300">Bean name filter</span>
            <input className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 outline-none" value={filters.beanName} onChange={(event) => setFilters((prev) => ({ ...prev, beanName: event.target.value }))} />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm text-slate-300">Rating filter</span>
            <select className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 outline-none" value={filters.rating} onChange={(event) => setFilters((prev) => ({ ...prev, rating: event.target.value }))}>
              <option value="">All</option>
              {[1, 2, 3, 4, 5].map((rating) => (
                <option key={rating} value={rating}>{rating}</option>
              ))}
            </select>
          </label>
          <div className="flex items-end">
            <button className="w-full rounded-xl border border-white/10 px-4 py-2 text-sm text-slate-100 transition hover:bg-white/5" onClick={() => load().catch(() => undefined)} type="button">Refresh</button>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="glass-panel overflow-hidden rounded-3xl">
          <table className="w-full text-left text-sm">
            <thead className="bg-white/5 text-slate-300">
              <tr>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Bean</th>
                <th className="px-4 py-3">EY</th>
                <th className="px-4 py-3">Rating</th>
                <th className="px-4 py-3">Time</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="cursor-pointer border-t border-white/5 transition hover:bg-white/5" onClick={async () => setSelected(await getBrewLog(log.id))}>
                  <td className="px-4 py-3 text-slate-300">{new Date(log.date).toLocaleString()}</td>
                  <td className="px-4 py-3">{log.bean_name ?? `Bean ${log.bean_id}`}</td>
                  <td className="px-4 py-3 text-amber-300">{log.yield_ey.toFixed(2)}%</td>
                  <td className="px-4 py-3">{log.rating}</td>
                  <td className="px-4 py-3">{log.elapsed_time_total.toFixed(1)}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="glass-panel rounded-3xl p-5">
          {selected ? (
            <>
              <h2 className="text-xl font-semibold">{selected.bean_name ?? `Bean ${selected.bean_id}`}</h2>
              <div className="mt-2 grid grid-cols-2 gap-3 text-sm text-slate-300">
                <div>Grind: {selected.grind_size}</div>
                <div>Dripper: {selected.dripper}</div>
                <div>Ratio: 1:{selected.brew_ratio.toFixed(1)}</div>
                <div>Days from roast: {selected.days_from_roast}</div>
                <div>Acidity: {selected.acidity}</div>
                <div>Sweetness: {selected.sweetness}</div>
                <div>Body: {selected.body}</div>
                <div>Rating: {selected.rating}</div>
              </div>

              {summary ? (
                <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
                  <div className="rounded-2xl bg-white/5 p-3">Peak weight: <span className="text-sky-300">{summary.peakWeight.toFixed(1)} g</span></div>
                  <div className="rounded-2xl bg-white/5 p-3">Avg flow: <span className="text-amber-300">{summary.avgFlow.toFixed(2)} g/s</span></div>
                  <div className="rounded-2xl bg-white/5 p-3">Max flow: <span className="text-emerald-300">{summary.maxFlow.toFixed(2)} g/s</span></div>
                </div>
              ) : null}

              <div className="mt-5 h-[360px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey="elapsed" stroke="#cbd5e1" />
                    <YAxis yAxisId="left" stroke="#cbd5e1" />
                    <YAxis yAxisId="right" orientation="right" stroke="#7dd3fc" />
                    <Tooltip contentStyle={{ background: "#0b1120", border: "1px solid rgba(125, 211, 252, 0.2)" }} />
                    <Line yAxisId="left" type="monotone" dataKey="weight" stroke="#7dd3fc" dot={false} strokeWidth={2} />
                    <Line yAxisId="left" type="monotone" dataKey="temp_kettle" stroke="#f59e0b" dot={false} strokeWidth={1.5} />
                    <Line yAxisId="left" type="monotone" dataKey="temp_dripper" stroke="#a78bfa" dot={false} strokeWidth={1.5} />
                    <Area yAxisId="right" type="monotone" dataKey="flow_rate" stroke="#34d399" fill="rgba(52, 211, 153, 0.15)" dot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </>
          ) : (
            <div className="flex h-full items-center justify-center text-slate-400">Select a brew log to inspect the replay chart.</div>
          )}
        </div>
      </div>
    </div>
  );
}
