"use client";

import { useState } from "react";
import { useDemoWebSocket } from "@/lib/ws";
import { SimulationView } from "@/components/center/SimulationView";
import { MissionRibbon } from "@/components/shell/MissionRibbon";
import { BciDrawer } from "@/components/shell/BciDrawer";
import { TaskDrawer } from "@/components/shell/TaskDrawer";

export default function Home() {
  useDemoWebSocket();
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);

  return (
    <div className="flex h-screen flex-col bg-white text-zinc-900">
      <MissionRibbon
        leftCollapsed={leftCollapsed}
        rightCollapsed={rightCollapsed}
        onToggleLeft={() => setLeftCollapsed((v) => !v)}
        onToggleRight={() => setRightCollapsed((v) => !v)}
      />
      <div className="flex flex-1 overflow-hidden">
        <BciDrawer
          collapsed={leftCollapsed}
          onToggle={() => setLeftCollapsed((v) => !v)}
        />
        <main className="flex flex-1 flex-col overflow-hidden p-3">
          <div className="flex flex-1 items-stretch">
            <div className="flex w-full flex-col">
              <SimulationView />
            </div>
          </div>
        </main>
        <TaskDrawer
          collapsed={rightCollapsed}
          onToggle={() => setRightCollapsed((v) => !v)}
        />
      </div>
    </div>
  );
}
