"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { archiveBean, getBean, getBrewLog, listBrewLogs } from "@/lib/api";
import type { Bean, BrewLog } from "@/lib/types";

type Props = {
  beanId: number;
};

export function BeanDetailView({ beanId }: Props) {
  const [bean, setBean] = useState<Bean | null>(null);
  const [logs, setLogs] = useState<BrewLog[]>([]);
  const [selectedLog, setSelectedLog] = useState<BrewLog | null>(null);
  const [loading, setLoading] = useState(true);
  const [savingArchive, setSavingArchive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [beanData, brewLogs] = await Promise.all([getBean(beanId), listBrewLogs({ beanId })]);
      setBean(beanData);
      setLogs(brewLogs);
      if (brewLogs.length > 0) {
        setSelectedLog((current) => current && brewLogs.some((log) => log.id === current.id) ? current : null);
      } else {
        setSelectedLog(null);
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load().catch(() => undefined);
  }, [beanId]);

  useEffect(() => {
    if (!selectedLog && logs.length > 0) {
      void selectLog(logs[0].id);
    }
  }, [logs, selectedLog]);

  const selectLog = async (logId: number) => {
    const detail = await getBrewLog(logId);
    setSelectedLog(detail);
  };

  const chartData = useMemo(() => selectedLog?.timeseries_json ?? [], [selectedLog]);
  const summary = useMemo(() => {
    if (logs.length === 0) return null;
    const avgRating = logs.reduce((sum, log) => sum + log.rating, 0) / logs.length;
    const avgEy = logs.reduce((sum, log) => sum + log.yield_ey, 0) / logs.length;
    const latest = logs[0];
    const best = logs.reduce((current, log) => (log.rating > current.rating ? log : current), logs[0]);
    return {
      avgRating,
      avgEy,
      latest,
      best,
    };
  }, [logs]);

  if (loading) {
    return <div className="glass-panel rounded-3xl p-6 text-slate-300">Loading bean detail…</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <Link className="text-sm text-sky-300 transition hover:text-sky-200" href="/">← Back to brew console</Link>
        <button
          className="rounded-xl border border-white/10 px-4 py-2 text-sm text-slate-100 transition hover:bg-white/5 disabled:opacity-60"
          disabled={!bean || savingArchive}
          onClick={async () => {
            if (!bean) return;
            setSavingArchive(true);
            try {
              await archiveBean(bean.id, !bean.is_archived);
              await load();
            } finally {
              setSavingArchive(false);
            }
          }}
          type="button"
        >
          {bean?.is_archived ? "Restore bean" : "Archive bean"}
        </button>
      </div>

      {error ? <div className="glass-panel rounded-3xl p-5 text-rose-300">{error}</div> : null}

      {bean ? (
        <>
          <section className="glass-panel rounded-3xl p-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.32em] text-sky-300/90">Bean detail</div>
                <h1 className="mt-2 text-3xl font-semibold">{bean.name}</h1>
                <p className="mt-2 text-sm text-slate-300">{bean.roaster}</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm text-slate-200 lg:min-w-[340px]">
                <div className="rounded-2xl bg-white/5 p-3">Process: {bean.process}</div>
                <div className="rounded-2xl bg-white/5 p-3">Level: {bean.roast_level}</div>
                <div className="rounded-2xl bg-white/5 p-3">Roast date: {bean.roast_date}</div>
                <div className="rounded-2xl bg-white/5 p-3">Age: {bean.days_from_roast ?? 0} days</div>
              </div>
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-4">
            <div className="glass-panel rounded-3xl p-5">
              <div className="text-sm text-slate-400">Brews</div>
              <div className="mt-2 text-3xl font-semibold">{logs.length}</div>
            </div>
            <div className="glass-panel rounded-3xl p-5">
              <div className="text-sm text-slate-400">Average rating</div>
              <div className="mt-2 text-3xl font-semibold">{summary ? summary.avgRating.toFixed(1) : "0.0"}</div>
            </div>
            <div className="glass-panel rounded-3xl p-5">
              <div className="text-sm text-slate-400">Average EY</div>
              <div className="mt-2 text-3xl font-semibold text-amber-300">{summary ? `${summary.avgEy.toFixed(2)}%` : "0.00%"}</div>
            </div>
            <div className="glass-panel rounded-3xl p-5">
              <div className="text-sm text-slate-400">Latest brew</div>
              <div className="mt-2 text-sm text-slate-200">{summary ? new Date(summary.latest.date).toLocaleString() : "—"}</div>
            </div>
            <div className="glass-panel rounded-3xl p-5 md:col-span-4">
              <div className="text-sm text-slate-400">Top brew</div>
              <div className="mt-2 text-sm text-slate-200">
                {summary ? `${new Date(summary.best.date).toLocaleString()} · Rating ${summary.best.rating} · EY ${summary.best.yield_ey.toFixed(2)}%` : "—"}
              </div>
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
            <div className="glass-panel overflow-hidden rounded-3xl">
              <table className="w-full text-left text-sm">
                <thead className="bg-white/5 text-slate-300">
                  <tr>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">EY</th>
                    <th className="px-4 py-3">Rating</th>
                    <th className="px-4 py-3">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id} className="cursor-pointer border-t border-white/5 transition hover:bg-white/5" onClick={() => void selectLog(log.id)}>
                      <td className="px-4 py-3 text-slate-300">{new Date(log.date).toLocaleString()}</td>
                      <td className="px-4 py-3 text-amber-300">{log.yield_ey.toFixed(2)}%</td>
                      <td className="px-4 py-3">{log.rating}</td>
                      <td className="px-4 py-3">{log.elapsed_time_total.toFixed(1)}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="glass-panel rounded-3xl p-5">
              {selectedLog ? (
                <>
                  <h2 className="text-xl font-semibold">Selected brew</h2>
                  <div className="mt-3 grid grid-cols-2 gap-3 text-sm text-slate-300">
                    <div>Extract: {selectedLog.extract_weight.toFixed(1)} g</div>
                    <div>Powder: {selectedLog.powder_weight.toFixed(1)} g</div>
                    <div>Ratio: 1:{selectedLog.brew_ratio.toFixed(1)}</div>
                    <div>Days from roast: {selectedLog.days_from_roast}</div>
                    <div>Grind: {selectedLog.grind_size}</div>
                    <div>Dripper: {selectedLog.dripper}</div>
                  </div>

                  <div className="mt-4 h-[340px]">
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
                <div className="flex h-full min-h-[420px] items-center justify-center text-slate-400">
                  Select a brew log to inspect the replay chart.
                </div>
              )}
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}
