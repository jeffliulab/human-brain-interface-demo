"use client";

import { IntentInput } from "@/components/center/IntentInput";
import { SessionHeader } from "@/components/bci/SessionHeader";
import { ChannelHealth } from "@/components/bci/ChannelHealth";
import { NeuralActivity } from "@/components/bci/NeuralActivity";
import { FiringRateBars } from "@/components/bci/FiringRateBars";
import { DecoderOutput } from "@/components/bci/DecoderOutput";

interface BciDrawerProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function BciDrawer({ collapsed, onToggle }: BciDrawerProps) {
  if (collapsed) {
    return (
      <aside className="flex w-12 shrink-0 flex-col items-center border-r border-zinc-200 bg-white/80 py-3">
        <button
          onClick={onToggle}
          title="展开 BCI 监控"
          className="flex h-10 w-10 items-center justify-center rounded border border-zinc-200 text-zinc-700 hover:border-sky-600 hover:text-sky-700"
        >
          <span className="text-lg leading-none">🧠</span>
        </button>
        <div className="mt-4 rotate-180 select-none text-[10px] uppercase tracking-widest text-zinc-600 [writing-mode:vertical-rl]">
          BCI Monitor
        </div>
      </aside>
    );
  }

  return (
    <aside className="flex w-80 shrink-0 flex-col gap-3 overflow-y-auto border-r border-zinc-200 bg-white/40 p-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-600">
          BCI 监控
        </h2>
        <button
          onClick={onToggle}
          title="收起"
          className="flex h-6 w-6 items-center justify-center rounded text-zinc-600 hover:bg-zinc-200 hover:text-zinc-800"
        >
          ◀
        </button>
      </div>
      <SessionHeader />
      <IntentInput />
      <ChannelHealth />
      <NeuralActivity />
      <FiringRateBars />
      <DecoderOutput />
    </aside>
  );
}
