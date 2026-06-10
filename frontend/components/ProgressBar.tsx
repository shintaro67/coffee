type ProgressBarProps = {
  progress: number;
};

export function ProgressBar({ progress }: ProgressBarProps) {
  const clamped = Math.min(Math.max(progress, 0), 1);
  return (
    <div className="glass-panel rounded-full p-2">
      <div className="h-4 overflow-hidden rounded-full bg-white/8">
        <div
          className="h-full rounded-full bg-gradient-to-r from-sky-400 via-cyan-300 to-amber-300 transition-all duration-150 ease-linear"
          style={{ width: `${clamped * 100}%` }}
        />
      </div>
      <div className="mt-2 text-right text-sm text-slate-300">{(clamped * 100).toFixed(1)}%</div>
    </div>
  );
}
