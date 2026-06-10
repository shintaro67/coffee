"use client";

import { useMemo, useState } from "react";

import { BeansView } from "@/components/BeansView";
import { BrewView } from "@/components/BrewView";
import { HistoryView } from "@/components/HistoryView";
import { useTelemetrySocket } from "@/hooks/useTelemetrySocket";

type ViewKey = "beans" | "brew" | "history";

export default function HomePage() {
  const socket = useTelemetrySocket();
  const [view, setView] = useState<ViewKey>("brew");

  const content = useMemo(() => {
    switch (view) {
      case "beans":
        return <BeansView />;
      case "history":
        return <HistoryView />;
      default:
        return <BrewView socket={socket} />;
    }
  }, [socket, view]);

  return (
    <main className="mx-auto max-w-[1600px] p-4 md:p-6">
      <header className="glass-panel rounded-3xl p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="text-xs uppercase tracking-[0.32em] text-sky-300/90">Coffee Brew Logger</div>
            <h1 className="mt-2 text-3xl font-semibold">FastAPI + Next.js realtime brew console</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-300">80Hz telemetry is rendered as numeric meters in Brew, while History recreates saved brew sessions with static charts.</p>
          </div>
          <nav className="flex gap-2 rounded-2xl border border-white/10 bg-white/5 p-2">
            {[
              ["beans", "🫘 Beans"],
              ["brew", "🔴 Brew"],
              ["history", "📊 History"],
            ].map(([key, label]) => (
              <button
                key={key}
                className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${view === key ? "bg-sky-400 text-slate-950" : "text-slate-200 hover:bg-white/5"}`}
                onClick={() => setView(key as ViewKey)}
                type="button"
              >
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <section className="mt-6">{content}</section>
    </main>
  );
}
