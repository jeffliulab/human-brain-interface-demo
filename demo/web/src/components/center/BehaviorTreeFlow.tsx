"use client";

import { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  type Edge,
  type Node,
} from "reactflow";
import "reactflow/dist/style.css";
import { useDemoStore } from "@/lib/store";
import type { BTStatus } from "@/types/taskspec";

const STATUS_STYLE: Record<BTStatus, { bg: string; border: string; label: string }> = {
  running: { bg: "#082f49", border: "#38bdf8", label: "RUNNING" },
  success: { bg: "#052e16", border: "#22c55e", label: "SUCCESS" },
  failure: { bg: "#450a0a", border: "#ef4444", label: "FAILURE" },
};

const IDLE = { bg: "#18181b", border: "#3f3f46", label: "IDLE" };

export function BehaviorTreeFlow() {
  const taskspec = useDemoStore((s) => s.taskspec);
  const btNodes = useDemoStore((s) => s.btNodes);

  const { nodes, edges } = useMemo<{ nodes: Node[]; edges: Edge[] }>(() => {
    if (!taskspec) return { nodes: [], edges: [] };
    const subtasks = taskspec.subtasks;

    const nodes: Node[] = [
      {
        id: "root",
        type: "default",
        data: { label: "Sequence (root)" },
        position: { x: 0, y: 0 },
        style: {
          background: "#1e1b4b",
          border: "1px solid #6366f1",
          color: "#c7d2fe",
          fontSize: 12,
          padding: 8,
          borderRadius: 6,
          width: 180,
        },
      },
      ...subtasks.map<Node>((st, i) => {
        const status = btNodes[st.name];
        const style = status ? STATUS_STYLE[status] : IDLE;
        return {
          id: st.name,
          type: "default",
          data: {
            label: (
              <div className="text-left">
                <div className="font-medium">{st.name}</div>
                <div className="mt-0.5 text-[9px] opacity-70">
                  {st.type} · {style.label}
                </div>
              </div>
            ),
          },
          position: { x: i * 200 - ((subtasks.length - 1) * 200) / 2, y: 130 },
          style: {
            background: style.bg,
            border: `1px solid ${style.border}`,
            color: "#e4e4e7",
            fontSize: 11,
            padding: 8,
            borderRadius: 6,
            width: 170,
          },
        };
      }),
    ];

    const edges: Edge[] = subtasks.map((st) => ({
      id: `root-${st.name}`,
      source: "root",
      target: st.name,
      animated: btNodes[st.name] === "running",
      style: { stroke: "#52525b" },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#52525b" },
    }));

    return { nodes, edges };
  }, [taskspec, btNodes]);

  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-4">
      <label className="text-xs uppercase tracking-wide text-zinc-600">
        L2/L3 · Behavior Tree
      </label>
      <div className="mt-2 h-64 w-full rounded bg-zinc-100/40">
        {taskspec ? (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            nodesDraggable={false}
            nodesConnectable={false}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#27272a" gap={16} />
            <Controls showInteractive={false} className="!bg-zinc-50 !border-zinc-300" />
          </ReactFlow>
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-zinc-600">
            behavior tree will build once TaskSpec arrives
          </div>
        )}
      </div>
    </div>
  );
}
