"use client";

import { useDemoStore } from "@/lib/store";
import type { LayerName } from "@/types/taskspec";
import clsx from "clsx";

interface LayerDef {
  id: LayerName;
  title: string;
  subtitle: string;
}

const LAYERS: LayerDef[] = [
  { id: "L0", title: "L0 · Input", subtitle: "Text → signal decorator" },
  { id: "L1", title: "L1 · Intent Parser", subtitle: "LLM → IntentToken" },
  { id: "L2", title: "L2 · Planner", subtitle: "TaskSpec → BehaviorTree" },
  { id: "L3", title: "L3 · Skill", subtitle: "Mock skill primitives" },
  { id: "L4", title: "L4 · Adapter", subtitle: "Device descriptor" },
  { id: "L5", title: "L5 · Assessment", subtitle: "ITA / MQA / SQA / GOA / PEA" },
];

export function LayerStack() {
  const activeLayer = useDemoStore((s) => s.activeLayer);

  return (
    <div className="space-y-2">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-600">
        Anima Stack
      </h2>
      <ul className="space-y-1.5">
        {LAYERS.map((l) => {
          const active = activeLayer === l.id;
          return (
            <li
              key={l.id}
              className={clsx(
                "rounded-md border px-3 py-2 transition-all",
                active
                  ? "border-sky-500 bg-sky-50 shadow-[0_0_0_1px_rgba(14,165,233,0.25)]"
                  : "border-zinc-200 bg-zinc-50/40"
              )}
            >
              <div className="flex items-center justify-between">
                <span
                  className={clsx(
                    "text-sm font-medium",
                    active ? "text-sky-700" : "text-zinc-800"
                  )}
                >
                  {l.title}
                </span>
                {active && (
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-sky-400" />
                )}
              </div>
              <p className="mt-0.5 text-[10px] text-zinc-600">{l.subtitle}</p>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
