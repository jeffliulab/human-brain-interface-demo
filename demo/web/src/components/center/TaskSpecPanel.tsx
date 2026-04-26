"use client";

import { useDemoStore } from "@/lib/store";

export function TaskSpecPanel() {
  const taskspec = useDemoStore((s) => s.taskspec);

  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-4">
      <label className="text-xs uppercase tracking-wide text-zinc-600">
        L1 · TaskSpec
      </label>
      {!taskspec ? (
        <p className="mt-3 text-xs text-zinc-600">
          TaskSpec will appear here after the LLM parse.
        </p>
      ) : (
        <div className="mt-3 space-y-3">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded bg-sky-100 px-2 py-0.5 font-mono text-sky-800">
              {taskspec.intent.token}
            </span>
            <span className="text-zinc-600">
              confidence{" "}
              <span className="font-mono text-zinc-800">
                {taskspec.intent.confidence.toFixed(3)}
              </span>
            </span>
            {taskspec.intent.requires_confirmation && (
              <span className="rounded bg-amber-100 px-2 py-0.5 text-amber-800">
                needs confirmation
              </span>
            )}
            <span className="text-zinc-600">
              drift {taskspec.intent.drift_score.toFixed(2)}
            </span>
          </div>
          {taskspec.intent.alternatives.length > 0 && (
            <div className="text-[11px] text-zinc-600">
              alternatives:{" "}
              {taskspec.intent.alternatives
                .map((a) => `${a.token} (${a.confidence.toFixed(2)})`)
                .join(" · ")}
            </div>
          )}
          <pre className="max-h-56 overflow-auto rounded bg-zinc-100/50 p-3 text-[11px] leading-relaxed text-zinc-700">
            {JSON.stringify(taskspec, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
