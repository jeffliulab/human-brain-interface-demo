import { create } from "zustand";
import type {
  AuditEntry,
  BTStatus,
  FiveFactors,
  LayerName,
  SignalFramePayload,
  TaskSpec,
} from "@/types/taskspec";

interface DemoState {
  activeLayer: LayerName | null;
  waveform: SignalFramePayload | null;
  taskspec: TaskSpec | null;
  btNodes: Record<string, BTStatus>;
  factors: FiveFactors;
  audit: AuditEntry[];
  wsConnected: boolean;

  setActiveLayer: (l: LayerName) => void;
  setWaveform: (w: SignalFramePayload) => void;
  setTaskspec: (t: TaskSpec) => void;
  updateBTNode: (node: string, status: BTStatus) => void;
  setFactors: (f: FiveFactors) => void;
  appendAudit: (entry: AuditEntry) => void;
  setWsConnected: (b: boolean) => void;
  reset: () => void;
}

const initialFactors: FiveFactors = {
  ita: 0,
  mqa: 1,
  sqa: 1,
  goa: 0,
  pea_count: 0,
};

export const useDemoStore = create<DemoState>((set) => ({
  activeLayer: null,
  waveform: null,
  taskspec: null,
  btNodes: {},
  factors: initialFactors,
  audit: [],
  wsConnected: false,

  setActiveLayer: (l) => set({ activeLayer: l }),
  setWaveform: (w) => set({ waveform: w }),
  setTaskspec: (t) =>
    set({
      taskspec: t,
      btNodes: Object.fromEntries(
        t.subtasks.map((s) => [s.name, "running" as BTStatus])
      ),
    }),
  updateBTNode: (node, status) =>
    set((s) => ({ btNodes: { ...s.btNodes, [node]: status } })),
  setFactors: (f) => set({ factors: f }),
  appendAudit: (entry) => set((s) => ({ audit: [entry, ...s.audit].slice(0, 20) })),
  setWsConnected: (b) => set({ wsConnected: b }),

  reset: () =>
    set({
      activeLayer: null,
      waveform: null,
      taskspec: null,
      btNodes: {},
      factors: initialFactors,
      audit: [],
    }),
}));
