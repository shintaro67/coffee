type MetricTileProps = {
  label: string;
  value: string;
  subtext?: string;
  tone?: "default" | "accent" | "warning";
};

export function MetricTile({ label, value, subtext, tone = "default" }: MetricTileProps) {
  const accent = tone === "accent" ? "text-sky-300" : tone === "warning" ? "text-amber-300" : "text-white";
  return (
    <div className="glass-panel rounded-2xl p-4">
      <div className="text-xs uppercase tracking-[0.24em] text-slate-400">{label}</div>
      <div className={`metric-value mt-2 text-3xl font-semibold ${accent}`}>{value}</div>
      {subtext ? <div className="mt-1 text-sm text-slate-400">{subtext}</div> : null}
    </div>
  );
}
