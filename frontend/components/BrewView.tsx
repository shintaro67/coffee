"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { listBeans, saveBrewLog } from "@/lib/api";
import { useTelemetrySelector } from "@/lib/telemetry-store";
import type { Bean, TelemetryPoint } from "@/lib/types";
import { MetricTile } from "./MetricTile";
import { ProgressBar } from "./ProgressBar";

type BrewFormState = {
  beanId: number | null;
  targetRatio: number;
  extractWeight: number;
  tds: number;
  grindSize: string;
  dripper: string;
  acidity: number;
  sweetness: number;
  body: number;
  rating: number;
  notes: string;
};

type BrewPoint = {
  elapsed: number;
  weight: number;
  temp_kettle: number;
  temp_dripper: number;
  flow_rate: number;
};

const initialForm: BrewFormState = {
  beanId: null,
  targetRatio: 15,
  extractWeight: 0,
  tds: 0,
  grindSize: "",
  dripper: "",
  acidity: 3,
  sweetness: 3,
  body: 3,
  rating: 3,
  notes: "",
};

export function BrewView({ socket }: { socket: { sendCommand: (command: "tare" | "start") => void } }) {
  const [beans, setBeans] = useState<Bean[]>([]);
  const [form, setForm] = useState<BrewFormState>(initialForm);
  const [saving, setSaving] = useState(false);
  const [powderWeight, setPowderWeight] = useState(0);
  const [targetWater, setTargetWater] = useState(0);
  const [isCollecting, setIsCollecting] = useState(false);
  const [brewFinished, setBrewFinished] = useState(false);
  const [brewPoints, setBrewPoints] = useState<BrewPoint[]>([]);

  const latest = useTelemetrySelector((state) => state.latestTelemetry);
  const flowRate = useTelemetrySelector((state) => state.smoothedFlowRate);
  const connected = useTelemetrySelector((state) => state.connected);

  const latestRef = useRef<TelemetryPoint | null>(latest);
  const flowRateRef = useRef(flowRate);

  useEffect(() => {
    latestRef.current = latest;
  }, [latest]);

  useEffect(() => {
    flowRateRef.current = flowRate;
  }, [flowRate]);

  useEffect(() => {
    listBeans().then(setBeans).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!form.beanId && beans.length > 0) {
      setForm((prev) => ({ ...prev, beanId: beans[0].id }));
    }
  }, [beans, form.beanId]);

  useEffect(() => {
    if (!isCollecting || brewFinished) {
      return undefined;
    }

    const interval = window.setInterval(() => {
      const current = latestRef.current;
      if (!current) {
        return;
      }

      setBrewPoints((prev) => {
        const next = [
          ...prev,
          {
            elapsed: current.elapsed,
            weight: current.weight,
            temp_kettle: current.temp_kettle,
            temp_dripper: current.temp_dripper,
            flow_rate: flowRateRef.current,
          },
        ];
        return next.length > 4000 ? next.slice(next.length - 4000) : next;
      });
    }, 50);

    return () => window.clearInterval(interval);
  }, [brewFinished, isCollecting]);

  useEffect(() => {
    if (!isCollecting || targetWater <= 0) {
      return;
    }

    const currentWeight = latest?.weight ?? 0;
    if (currentWeight >= targetWater) {
      setIsCollecting(false);
      setBrewFinished(true);
    }
  }, [isCollecting, latest?.weight, targetWater]);

  const bean = useMemo(() => beans.find((entry) => entry.id === form.beanId) ?? null, [beans, form.beanId]);
  const currentWeight = latest?.weight ?? 0;
  const elapsed = latest?.elapsed ?? 0;
  const progress = targetWater > 0 ? Math.min(currentWeight / targetWater, 1) : 0;
  const currentRatio = powderWeight > 0 ? currentWeight / powderWeight : 0;
  const ey = powderWeight > 0 ? (form.extractWeight * form.tds) / powderWeight : 0;

  return (
    <div className="space-y-6">
      <div className="glass-panel rounded-3xl p-5">
        <div className="flex flex-wrap items-center gap-3">
          <div className="text-sm text-slate-400">Connection</div>
          <div className={`rounded-full px-3 py-1 text-xs font-semibold ${connected ? "bg-emerald-400/20 text-emerald-300" : "bg-rose-400/20 text-rose-300"}`}>
            {connected ? "Live" : "Offline"}
          </div>
          <div className={`rounded-full px-3 py-1 text-xs font-semibold ${brewFinished ? "bg-emerald-400/20 text-emerald-300" : isCollecting ? "bg-sky-400/20 text-sky-300" : "bg-white/5 text-slate-300"}`}>
            {brewFinished ? "finished" : isCollecting ? "brewing" : "idle"}
          </div>
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-[1.2fr_1fr]">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <label className="block">
              <span className="mb-1 block text-sm text-slate-300">Bean</span>
              <select
                className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 outline-none"
                value={form.beanId ?? ""}
                onChange={(event) => setForm((prev) => ({ ...prev, beanId: Number(event.target.value) }))}
              >
                {beans.map((entry) => (
                  <option key={entry.id} value={entry.id}>
                    {entry.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-1 block text-sm text-slate-300">Target ratio (1:X)</span>
              <input
                type="number"
                step="0.1"
                className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 outline-none"
                value={form.targetRatio}
                onChange={(event) => setForm((prev) => ({ ...prev, targetRatio: Number(event.target.value) }))}
              />
            </label>
            <div className="flex items-end gap-3">
              <button
                className="flex-1 rounded-xl border border-white/10 px-4 py-3 font-semibold text-white transition hover:bg-white/5"
                onClick={() => {
                  socket.sendCommand("tare");
                  setPowderWeight(0);
                  setTargetWater(0);
                  setIsCollecting(false);
                  setBrewFinished(false);
                  setBrewPoints([]);
                }}
                type="button"
              >
                Tare
              </button>
              <button
                className="flex-1 rounded-xl bg-sky-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-sky-300"
                onClick={() => {
                  const capturedPowder = latest?.weight ?? 0;
                  const calculatedTargetWater = capturedPowder * form.targetRatio;
                  setPowderWeight(capturedPowder);
                  setTargetWater(calculatedTargetWater);
                  setBrewPoints([]);
                  setIsCollecting(true);
                  setBrewFinished(false);
                  socket.sendCommand("start");
                }}
                type="button"
              >
                Start
              </button>
            </div>
            <div className="flex items-end text-sm text-slate-400">Latest weight on Start is captured as powder weight.</div>
          </div>

          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <MetricTile label="Powder (g)" value={powderWeight.toFixed(2)} />
            <MetricTile label="Elapsed (s)" value={elapsed.toFixed(1)} />
            <MetricTile label="Weight (g)" value={currentWeight.toFixed(2)} subtext={`Target ${targetWater.toFixed(2)} g`} tone="accent" />
            <MetricTile label="Ratio (1:X)" value={currentRatio > 0 ? currentRatio.toFixed(2) : "0.00"} />
            <MetricTile label="Flow (g/s)" value={flowRate.toFixed(2)} tone="warning" />
            <MetricTile label="Temp Kettle" value={(latest?.temp_kettle ?? 0).toFixed(1)} />
            <MetricTile label="Temp Dripper" value={(latest?.temp_dripper ?? 0).toFixed(1)} />
            <MetricTile label="State" value={brewFinished ? "finished" : isCollecting ? "brewing" : "idle"} />
          </div>
        </div>

        <div className="mt-5">
          <ProgressBar progress={progress} />
          {brewFinished ? <p className="mt-3 text-sm text-emerald-300">Pour completed. Save form is ready.</p> : null}
        </div>
      </div>

      <div className={`glass-panel rounded-3xl p-5 ${brewFinished ? "block" : "opacity-90"}`}>
        <h2 className="text-xl font-semibold">Save BrewLog</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <label className="block">
            <span className="mb-1 block text-sm text-slate-300">Extract weight (g)</span>
            <input
              type="number"
              min="0"
              step="0.1"
              className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 outline-none"
              value={form.extractWeight}
              onChange={(event) => setForm((prev) => ({ ...prev, extractWeight: Number(event.target.value) }))}
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm text-slate-300">TDS (%)</span>
            <input
              type="number"
              min="0"
              max="20"
              step="0.1"
              className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 outline-none"
              value={form.tds}
              onChange={(event) => setForm((prev) => ({ ...prev, tds: Number(event.target.value) }))}
            />
          </label>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-sm text-slate-400">EY preview</div>
            <div className="metric-value mt-2 text-3xl font-semibold text-amber-300">{ey.toFixed(2)}%</div>
          </div>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="block">
            <span className="mb-1 block text-sm text-slate-300">Grind size</span>
            <input className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 outline-none" value={form.grindSize} onChange={(event) => setForm((prev) => ({ ...prev, grindSize: event.target.value }))} />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm text-slate-300">Dripper</span>
            <input className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 outline-none" value={form.dripper} onChange={(event) => setForm((prev) => ({ ...prev, dripper: event.target.value }))} />
          </label>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-4">
          {[
            ["acidity", "Acidity"],
            ["sweetness", "Sweetness"],
            ["body", "Body"],
            ["rating", "Rating"],
          ].map(([key, label]) => (
            <label key={key} className="block">
              <span className="mb-1 block text-sm text-slate-300">{label}</span>
              <input
                type="range"
                min="1"
                max="5"
                value={form[key as keyof BrewFormState] as number}
                onChange={(event) => setForm((prev) => ({ ...prev, [key]: Number(event.target.value) }))}
                className="w-full"
              />
              <div className="mt-1 text-sm text-slate-400">{form[key as keyof BrewFormState] as number}</div>
            </label>
          ))}
        </div>

        <label className="mt-4 block">
          <span className="mb-1 block text-sm text-slate-300">Notes</span>
          <textarea className="min-h-24 w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 outline-none" value={form.notes} onChange={(event) => setForm((prev) => ({ ...prev, notes: event.target.value }))} />
        </label>

        <button
          disabled={!brewFinished || saving}
          className="mt-4 rounded-xl bg-amber-300 px-4 py-3 font-semibold text-slate-950 transition hover:bg-amber-200 disabled:cursor-not-allowed disabled:opacity-50"
          onClick={async () => {
            setSaving(true);
            try {
              const payload = {
                bean_id: bean?.id ?? form.beanId,
                days_from_roast: bean?.days_from_roast ?? 0,
                elapsed_time_total: elapsed,
                max_weight: currentWeight,
                powder_weight: powderWeight,
                extract_weight: form.extractWeight,
                tds: form.tds,
                brew_ratio: form.targetRatio,
                grind_size: form.grindSize,
                dripper: form.dripper,
                acidity: form.acidity,
                sweetness: form.sweetness,
                body: form.body,
                rating: form.rating,
                notes: form.notes,
                timeseries_json: brewPoints,
              };
              await saveBrewLog(payload);
              setForm(initialForm);
              setPowderWeight(0);
              setTargetWater(0);
              setIsCollecting(false);
              setBrewFinished(false);
              setBrewPoints([]);
            } finally {
              setSaving(false);
            }
          }}
          type="button"
        >
          {saving ? "Saving..." : "Save BrewLog"}
        </button>
      </div>
    </div>
  );
}
