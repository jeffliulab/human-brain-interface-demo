"use client";

import { useDemoStore } from "@/lib/store";

interface FactorDef {
  key: "ita" | "mqa" | "sqa" | "goa";
  label: string;
  full: string;
  hue: number;
}

const FACTORS: FactorDef[] = [
  { key: "ita", label: "ITA", full: "Intent Trust", hue: 200 },
  { key: "mqa", label: "MQA", full: "Motor Quality", hue: 170 },
  { key: "sqa", label: "SQA", full: "Sensing Quality", hue: 260 },
  { key: "goa", label: "GOA", full: "Goal Outcome", hue: 140 },
];

function Ring({ value, hue, label }: { value: number; hue: number; label: string }) {
  const pct = Math.max(0, Math.min(1, value));
  const r = 26;
  const c = 2 * Math.PI * r;
  const dash = c * pct;
  return (
    <div className="flex flex-col items-center">
      <svg width="72" height="72" viewBox="0 0 72 72">
        <circle
          cx="36" cy="36" r={r}
          fill="none"
          stroke="#27272a"
          strokeWidth="6"
        />
        <circle
          cx="36" cy="36" r={r}
          fill="none"
          stroke={`hsl(${hue} 85% 55%)`}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${c - dash}`}
          transform="rotate(-90 36 36)"
          className="transition-all duration-500"
        />
        <text
          x="36" y="40"
          textAnchor="middle"
          className="fill-zinc-900 font-mono"
          fontSize="13"
        >
          {value.toFixed(2)}
        </text>
      </svg>
      <span className="text-[10px] font-semibold tracking-wide text-zinc-700">
        {label}
      </span>
    </div>
  );
}

export function FiveFactorPanel() {
  const factors = useDemoStore((s) => s.factors);

  return (
    <div className="space-y-3">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-600">
        Five Factors
      </h2>
      <div className="grid grid-cols-2 gap-3 rounded-lg border border-zinc-200 bg-zinc-50/50 p-3">
        {FACTORS.map((f) => (
          <div key={f.key} className="flex flex-col items-center gap-1">
            <Ring value={factors[f.key]} hue={f.hue} label={f.label} />
            <span className="text-[9px] text-zinc-600">{f.full}</span>
          </div>
        ))}
      </div>
      <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-4">
        <div className="flex items-baseline justify-between">
          <div>
            <div className="text-xs font-semibold text-zinc-700">PEA</div>
            <div className="text-[10px] text-zinc-600">Posterior Evidence</div>
          </div>
          <div className="font-mono text-2xl font-semibold text-emerald-700">
            {factors.pea_count}
          </div>
        </div>
        <p className="mt-2 text-[10px] leading-snug text-zinc-600">
          Append-only evidence log; each successful run increments once.
        </p>
      </div>
    </div>
  );
}
