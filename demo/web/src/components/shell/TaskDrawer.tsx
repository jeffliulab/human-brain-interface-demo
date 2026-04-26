"use client";

import { TaskSpecPanel } from "@/components/center/TaskSpecPanel";
import { BehaviorTreeFlow } from "@/components/center/BehaviorTreeFlow";
import { FiveFactorPanel } from "@/components/factors/FiveFactorPanel";
import { IntentTokenStream } from "@/components/center/IntentTokenStream";
import { LayerStack } from "@/components/layers/LayerStack";
import { useDemoStore } from "@/lib/store";
import type { BTStatus } from "@/types/taskspec";

interface TaskDrawerProps {
  collapsed: boolean;
  onToggle: () => void;
}

const DOT_STYLE: Record<BTStatus | "idle", string> = {
  idle: "bg-zinc-300 text-zinc-700",
  running: "bg-sky-600 text-sky-100 animate-pulse",
  success: "bg-emerald-600 text-emerald-50",
  failure: "bg-rose-600 text-rose-50",
};

function IntentDecodeCard() {
  const taskspec = useDemoStore((s) => s.taskspec);
  if (!taskspec) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-3">
        <label className="text-xs uppercase tracking-wide text-zinc-600">
          Intent Decode
        </label>
        <p className="mt-2 text-[11px] text-zinc-600">
          awaiting intent — send a command to decode.
        </p>
      </div>
    );
  }
  const { token, confidence, drift_score, alternatives } = taskspec.intent;
  const conf = Math.max(0, Math.min(1, confidence));
  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-3">
      <label className="text-xs uppercase tracking-wide text-zinc-600">
        Intent Decode
      </label>
      <div className="mt-2 flex items-baseline justify-between">
        <span className="rounded bg-sky-100 px-2 py-0.5 font-mono text-sm text-sky-800">
          {token}
        </span>
        <span className="font-mono text-lg text-zinc-900">{conf.toFixed(2)}</span>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-zinc-200">
        <div
          className="h-full bg-sky-500 transition-all duration-500"
          style={{ width: `${conf * 100}%` }}
        />
      </div>
      <div className="mt-2 text-[10px] text-zinc-600">
        drift {drift_score.toFixed(2)}
        {alternatives.length > 0 && (
          <>
            {" · alt "}
            {alternatives
              .slice(0, 2)
              .map((a) => `${a.token} ${a.confidence.toFixed(2)}`)
              .join(", ")}
          </>
        )}
      </div>
    </div>
  );
}

function BtPipelineStrip() {
  const taskspec = useDemoStore((s) => s.taskspec);
  const btNodes = useDemoStore((s) => s.btNodes);

  if (!taskspec) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-3">
        <label className="text-xs uppercase tracking-wide text-zinc-600">
          BT Pipeline
        </label>
        <p className="mt-2 text-[11px] text-zinc-600">
          pipeline appears after TaskSpec arrives.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-3">
      <label className="text-xs uppercase tracking-wide text-zinc-600">
        BT Pipeline
      </label>
      <ol className="mt-2 space-y-1">
        {taskspec.subtasks.map((st, i) => {
          const status = btNodes[st.name] ?? "idle";
          const cls = DOT_STYLE[status];
          return (
            <li key={st.name} className="flex items-center gap-2 text-xs">
              <span
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-mono ${cls}`}
              >
                {i + 1}
              </span>
              <span className="font-mono text-zinc-800">{st.name}</span>
              <span className="text-[10px] text-zinc-600">{st.type}</span>
              <span
                className={`ml-auto text-[10px] font-mono ${
                  status === "success"
                    ? "text-emerald-700"
                    : status === "failure"
                    ? "text-rose-700"
                    : status === "running"
                    ? "text-sky-700"
                    : "text-zinc-600"
                }`}
              >
                {status.toUpperCase()}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

export function TaskDrawer({ collapsed, onToggle }: TaskDrawerProps) {
  if (collapsed) {
    return (
      <aside className="flex w-12 shrink-0 flex-col items-center border-l border-zinc-200 bg-white/80 py-3">
        <button
          onClick={onToggle}
          title="展开任务执行"
          className="flex h-10 w-10 items-center justify-center rounded border border-zinc-200 text-zinc-700 hover:border-sky-600 hover:text-sky-700"
        >
          <span className="text-lg leading-none">⚙</span>
        </button>
        <div className="mt-4 select-none text-[10px] uppercase tracking-widest text-zinc-600 [writing-mode:vertical-rl]">
          Task Execution
        </div>
      </aside>
    );
  }

  return (
    <aside className="flex w-80 shrink-0 flex-col gap-3 overflow-y-auto border-l border-zinc-200 bg-white/40 p-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-600">
          任务执行 · Anima
        </h2>
        <button
          onClick={onToggle}
          title="收起"
          className="flex h-6 w-6 items-center justify-center rounded text-zinc-600 hover:bg-zinc-200 hover:text-zinc-800"
        >
          ▶
        </button>
      </div>
      <IntentDecodeCard />
      <LayerStack />
      <BtPipelineStrip />
      <BehaviorTreeFlow />
      <FiveFactorPanel />
      <TaskSpecPanel />
      <IntentTokenStream />
    </aside>
  );
}
