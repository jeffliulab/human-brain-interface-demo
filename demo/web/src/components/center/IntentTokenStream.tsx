"use client";

import { useDemoStore } from "@/lib/store";

function outcomeStyle(o: "success" | "fail" | "cancel") {
  if (o === "success") return "text-emerald-800 bg-emerald-100 border-emerald-300";
  if (o === "fail") return "text-rose-800 bg-rose-100 border-rose-300";
  return "text-amber-800 bg-amber-100 border-amber-300";
}

export function IntentTokenStream() {
  const audit = useDemoStore((s) => s.audit);

  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-4">
      <label className="text-xs uppercase tracking-wide text-zinc-600">
        Intent Token Stream
      </label>
      {audit.length === 0 ? (
        <p className="mt-3 text-xs text-zinc-600">
          tokens accumulate as intents complete.
        </p>
      ) : (
        <ul className="mt-2 max-h-48 space-y-1 overflow-auto pr-1">
          {audit.map((e, i) => {
            const ts = new Date(e.timestamp);
            const hh = ts.toLocaleTimeString(undefined, { hour12: false });
            return (
              <li
                key={`${e.timestamp}-${i}`}
                className={`flex items-center justify-between gap-2 rounded border px-2 py-1 text-xs ${outcomeStyle(e.outcome)}`}
              >
                <span className="font-mono">{e.intent}</span>
                <span className="text-[10px] opacity-70">
                  {e.outcome} · {hh}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
