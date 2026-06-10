"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { archiveBean, createBean, listBeans } from "@/lib/api";
import type { Bean } from "@/lib/types";

const initialForm = {
  name: "",
  roaster: "",
  process: "Washed",
  roast_level: "Light",
  roast_date: new Date().toISOString().slice(0, 10),
};

export function BeansView() {
  const [beans, setBeans] = useState<Bean[]>([]);
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    const data = await listBeans();
    setBeans(data);
  };

  useEffect(() => {
    load().catch((err) => setError(String(err)));
  }, []);

  const sortedBeans = useMemo(() => beans.slice().sort((a, b) => (b.days_from_roast ?? 0) - (a.days_from_roast ?? 0)), [beans]);

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
        <form
          className="glass-panel rounded-3xl p-5"
          onSubmit={async (event) => {
            event.preventDefault();
            setLoading(true);
            setError(null);
            try {
              await createBean(form);
              setForm(initialForm);
              await load();
            } catch (err) {
              setError(String(err));
            } finally {
              setLoading(false);
            }
          }}
        >
          <h2 className="text-xl font-semibold">Beans</h2>
          <div className="mt-4 space-y-3">
            {[
              ["name", "Bean name"],
              ["roaster", "Roaster / Farm"],
            ].map(([key, label]) => (
              <label key={key} className="block">
                <span className="mb-1 block text-sm text-slate-300">{label}</span>
                <input
                  className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 outline-none focus:border-sky-300"
                  value={form[key as keyof typeof form]}
                  onChange={(event) => setForm((prev) => ({ ...prev, [key]: event.target.value }))}
                />
              </label>
            ))}
            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="mb-1 block text-sm text-slate-300">Process</span>
                <input className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 outline-none focus:border-sky-300" value={form.process} onChange={(event) => setForm((prev) => ({ ...prev, process: event.target.value }))} />
              </label>
              <label className="block">
                <span className="mb-1 block text-sm text-slate-300">Roast level</span>
                <input className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 outline-none focus:border-sky-300" value={form.roast_level} onChange={(event) => setForm((prev) => ({ ...prev, roast_level: event.target.value }))} />
              </label>
            </div>
            <label className="block">
              <span className="mb-1 block text-sm text-slate-300">Roast date</span>
              <input type="date" className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 outline-none focus:border-sky-300" value={form.roast_date} onChange={(event) => setForm((prev) => ({ ...prev, roast_date: event.target.value }))} />
            </label>
          </div>
          {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
          <button disabled={loading} className="mt-5 w-full rounded-xl bg-sky-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-sky-300 disabled:opacity-60">
            {loading ? "Saving..." : "Register bean"}
          </button>
        </form>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {sortedBeans.map((bean) => (
            <article key={bean.id} className="glass-panel rounded-3xl p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold">{bean.name}</h3>
                  <p className="mt-1 text-sm text-slate-400">{bean.roaster}</p>
                </div>
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">{bean.days_from_roast ?? 0}d</span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-sm text-slate-300">
                <div>Process: {bean.process}</div>
                <div>Level: {bean.roast_level}</div>
                <div>Roast date: {bean.roast_date}</div>
                <div>Status: {bean.is_archived ? "Archived" : "Active"}</div>
              </div>
              <button
                className="mt-4 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-100 transition hover:bg-white/5"
                onClick={async () => {
                  await archiveBean(bean.id, !bean.is_archived);
                  await load();
                }}
              >
                {bean.is_archived ? "Restore" : "Archive"}
              </button>
              <Link
                className="mt-3 block rounded-xl border border-white/10 px-3 py-2 text-center text-sm text-sky-300 transition hover:bg-white/5"
                href={`/beans/${bean.id}`}
              >
                Open detail
              </Link>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
