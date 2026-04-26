"use client";

import { useEffect, useState } from "react";
import { useDemoStore } from "@/lib/store";

export function SessionHeader() {
  const taskspec = useDemoStore((s) => s.taskspec);
  const wsConnected = useDemoStore((s) => s.wsConnected);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [now, setNow] = useState(0);

  useEffect(() => {
    if (taskspec && startedAt === null) setStartedAt(Date.now());
  }, [taskspec, startedAt]);

  useEffect(() => {
    if (startedAt === null) return;
    const id = setInterval(() => setNow(Date.now()), 200);
    return () => clearInterval(id);
  }, [startedAt]);

  const recording = startedAt !== null;
  const elapsed = recording ? now - startedAt! : 0;
  const mm = Math.floor(elapsed / 60000).toString().padStart(2, "0");
  const ss = Math.floor((elapsed % 60000) / 1000).toString().padStart(2, "0");

  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 px-3 py-2">
      <div className="flex items-center justify-between text-[11px]">
        <div className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${
              recording ? "animate-pulse bg-rose-500" : "bg-zinc-300"
            }`}
          />
          <span
            className={`font-mono font-semibold tracking-wider ${
              recording ? "text-rose-700" : "text-zinc-600"
            }`}
          >
            {recording ? "REC" : "IDLE"}
          </span>
          <span className="font-mono tabular-nums text-zinc-800">
            {mm}:{ss}
          </span>
        </div>
        <div className="flex items-center gap-2 font-mono text-zinc-600">
          <span className={wsConnected ? "text-emerald-700" : "text-rose-700"}>
            {wsConnected ? "250" : "—"}
          </span>
          <span className="text-zinc-600">/ 250 Hz</span>
        </div>
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-zinc-600">
        <span>session · patient-001</span>
        <span className="font-mono">dropped 0</span>
      </div>
    </div>
  );
}
