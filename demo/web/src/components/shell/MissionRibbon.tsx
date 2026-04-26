"use client";

import { useEffect, useState } from "react";
import { useDemoStore } from "@/lib/store";

interface MissionRibbonProps {
  leftCollapsed: boolean;
  rightCollapsed: boolean;
  onToggleLeft: () => void;
  onToggleRight: () => void;
}

function useMissionClock(taskspec: ReturnType<typeof useDemoStore.getState>["taskspec"]) {
  const [elapsed, setElapsed] = useState(0);
  const [startedAt, setStartedAt] = useState<number | null>(null);

  useEffect(() => {
    if (taskspec) {
      setStartedAt(Date.now());
      setElapsed(0);
    } else {
      setStartedAt(null);
      setElapsed(0);
    }
  }, [taskspec]);

  useEffect(() => {
    if (startedAt === null) return;
    const id = setInterval(() => setElapsed(Date.now() - startedAt), 100);
    return () => clearInterval(id);
  }, [startedAt]);

  const mm = Math.floor(elapsed / 60_000).toString().padStart(2, "0");
  const ss = Math.floor((elapsed % 60_000) / 1000).toString().padStart(2, "0");
  const ms = Math.floor((elapsed % 1000) / 100);
  return `T+${mm}:${ss}.${ms}`;
}

export function MissionRibbon({
  leftCollapsed,
  rightCollapsed,
  onToggleLeft,
  onToggleRight,
}: MissionRibbonProps) {
  const taskspec = useDemoStore((s) => s.taskspec);
  const wsConnected = useDemoStore((s) => s.wsConnected);
  const clock = useMissionClock(taskspec);

  const intent = taskspec?.intent.token ?? "—";
  const confidence = taskspec?.intent.confidence;

  return (
    <header className="flex h-12 shrink-0 items-center justify-between border-b border-zinc-200 bg-white px-3 text-xs">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleLeft}
          title={leftCollapsed ? "展开 BCI 监控" : "收起 BCI 监控"}
          className="flex h-8 w-8 items-center justify-center rounded border border-zinc-200 text-zinc-700 hover:border-sky-600 hover:text-sky-700"
        >
          <span className="text-base leading-none">{leftCollapsed ? "▶" : "◀"}</span>
        </button>
        <div className="flex items-baseline gap-3">
          <span className="text-zinc-600">患者</span>
          <span className="font-mono text-zinc-900">001 · 病房 3B</span>
          <span className="text-zinc-600">·</span>
          <span className="text-zinc-600">任务</span>
          <span className="font-mono text-sky-700">drink-water</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-baseline gap-2">
          <span className="text-zinc-500">Intent</span>
          <span className="font-mono text-zinc-900">{intent}</span>
          {confidence !== undefined && (
            <span className="font-mono text-zinc-500">
              · {confidence.toFixed(2)}
            </span>
          )}
        </div>
        <div className="font-mono tabular-nums text-zinc-700">{clock}</div>
        <div className="flex items-center gap-1">
          <span
            className={`h-2 w-2 rounded-full ${
              wsConnected ? "animate-pulse bg-emerald-400" : "bg-rose-500"
            }`}
          />
          <span className={wsConnected ? "text-emerald-700" : "text-rose-700"}>
            {wsConnected ? "Live" : "Offline"}
          </span>
        </div>
        <button
          onClick={onToggleRight}
          title={rightCollapsed ? "展开任务执行" : "收起任务执行"}
          className="flex h-8 w-8 items-center justify-center rounded border border-zinc-200 text-zinc-700 hover:border-sky-600 hover:text-sky-700"
        >
          <span className="text-base leading-none">{rightCollapsed ? "◀" : "▶"}</span>
        </button>
      </div>
    </header>
  );
}
