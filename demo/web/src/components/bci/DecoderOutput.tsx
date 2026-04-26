"use client";

import { useDemoStore } from "@/lib/store";

const DIRECTION: Record<string, [number, number]> = {
  DRINK_WATER: [0.8, 0.3],
  LIFT: [0.1, 0.9],
  NAVIGATE: [0.7, 0.0],
  GRASP: [0.5, 0.5],
  IDLE: [0, 0],
};

export function DecoderOutput() {
  const taskspec = useDemoStore((s) => s.taskspec);
  const token = taskspec?.intent.token ?? "IDLE";
  const confidence = taskspec?.intent.confidence ?? 0;
  const [vx, vy] = DIRECTION[token] ?? [0.4, 0.4];
  const arrowX = 60 + vx * 40;
  const arrowY = 60 - vy * 40;

  const bps = taskspec ? Math.round(confidence * 9 * 10) / 10 : 0;
  const bpsPct = Math.min(100, (bps / 10) * 100);

  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-3">
      <div className="flex items-center justify-between">
        <label className="text-xs uppercase tracking-wide text-zinc-600">
          Decoder Output
        </label>
        <span className="text-[9px] font-mono text-zinc-600">velocity · BPS</span>
      </div>
      <div className="mt-2 flex items-start gap-3">
        <svg
          width="120"
          height="120"
          viewBox="0 0 120 120"
          className="shrink-0 rounded bg-zinc-100/50"
        >
          <circle
            cx="60"
            cy="60"
            r="42"
            fill="none"
            stroke="#3f3f46"
            strokeWidth="1"
            strokeDasharray="2 3"
          />
          <line x1="18" y1="60" x2="102" y2="60" stroke="#27272a" strokeWidth="0.5" />
          <line x1="60" y1="18" x2="60" y2="102" stroke="#27272a" strokeWidth="0.5" />
          {taskspec && (
            <>
              <line
                x1="60"
                y1="60"
                x2={arrowX}
                y2={arrowY}
                stroke="#38bdf8"
                strokeWidth="2"
              />
              <circle cx={arrowX} cy={arrowY} r="3" fill="#38bdf8" />
            </>
          )}
          <text
            x="60"
            y="114"
            textAnchor="middle"
            fontSize="8"
            fill="#71717a"
            fontFamily="ui-monospace"
          >
            ({vx.toFixed(2)}, {vy.toFixed(2)})
          </text>
        </svg>
        <div className="flex-1 text-[10px]">
          <div className="text-zinc-600">decoded token</div>
          <div className="mt-0.5 font-mono text-sky-700">{token}</div>
          <div className="mt-2 text-zinc-600">BPS (target 8)</div>
          <div className="relative mt-0.5 h-2 w-full overflow-hidden rounded-sm bg-zinc-50">
            <div
              className="h-full bg-sky-400"
              style={{ width: `${bpsPct}%` }}
            />
            <div className="absolute top-0 h-full w-[1px] bg-amber-400" style={{ left: "80%" }} />
          </div>
          <div className="mt-1 flex justify-between font-mono tabular-nums text-zinc-600">
            <span>{bps.toFixed(1)}</span>
            <span className="text-zinc-600">bits/s</span>
          </div>
          <div className="mt-2 text-zinc-600">confidence</div>
          <div className="mt-0.5 font-mono text-zinc-800">{confidence.toFixed(2)}</div>
        </div>
      </div>
    </div>
  );
}
