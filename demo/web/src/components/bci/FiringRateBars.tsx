"use client";

import { useDemoStore } from "@/lib/store";

export function FiringRateBars() {
  const waveform = useDemoStore((s) => s.waveform);
  const channels = waveform?.channels?.slice(0, 16) ?? [];

  const rates = Array.from({ length: 16 }, (_, i) => {
    const frames = channels[i];
    if (!frames || frames.length === 0) return 0;
    const sumAbs = frames.reduce((a, v) => a + Math.abs(v), 0);
    return Math.min(100, Math.round((sumAbs / frames.length) * 140));
  });

  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-3">
      <div className="flex items-center justify-between">
        <label className="text-xs uppercase tracking-wide text-zinc-600">
          Firing Rate
        </label>
        <span className="text-[9px] font-mono text-zinc-600">Hz · 200 ms win</span>
      </div>
      <div className="mt-2 grid grid-cols-1 gap-[2px]">
        {rates.map((r, i) => {
          const pct = Math.min(100, r);
          const barColor =
            r === 0
              ? "bg-zinc-200"
              : r > 60
              ? "bg-amber-400"
              : r > 30
              ? "bg-sky-400"
              : "bg-sky-700";
          return (
            <div key={i} className="flex items-center gap-1 text-[9px]">
              <span className="w-10 shrink-0 font-mono text-zinc-600">
                {(i + 1).toString().padStart(2, "0")}
              </span>
              <div className="relative h-2 flex-1 overflow-hidden rounded-sm bg-zinc-50">
                <div
                  className={`h-full ${barColor} transition-all duration-300`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="w-6 shrink-0 text-right font-mono tabular-nums text-zinc-600">
                {r}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
