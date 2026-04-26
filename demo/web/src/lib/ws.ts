import { useEffect, useRef } from "react";

import { useDemoStore } from "@/lib/store";
import type {
  AuditEntry,
  BTTickEvent,
  FiveFactors,
  LayerName,
  SignalFramePayload,
  TaskSpec,
  WSEvent,
} from "@/types/taskspec";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8765/ws";

export function useDemoWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;
    const store = useDemoStore.getState();

    ws.onopen = () => store.setWsConnected(true);
    ws.onclose = () => store.setWsConnected(false);
    ws.onerror = () => store.setWsConnected(false);

    ws.onmessage = (msg) => {
      try {
        const evt = JSON.parse(msg.data) as WSEvent;
        dispatch(evt);
      } catch (e) {
        console.error("bad ws msg", e);
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, []);

  return wsRef;
}

function dispatch(evt: WSEvent) {
  const s = useDemoStore.getState();
  switch (evt.event) {
    case "layer.activate": {
      const d = evt.data as { layer: LayerName };
      s.setActiveLayer(d.layer);
      return;
    }
    case "signal.frame":
      s.setWaveform(evt.data as SignalFramePayload);
      return;
    case "taskspec.ready":
      s.setTaskspec(evt.data as TaskSpec);
      return;
    case "factor.update":
      s.setFactors(evt.data as FiveFactors);
      return;
    case "bt.tick": {
      const d = evt.data as BTTickEvent;
      s.updateBTNode(d.node, d.status);
      return;
    }
    case "audit.append":
      s.appendAudit(evt.data as AuditEntry);
      return;
    case "session.hello":
      return;
    default:
      console.debug("unhandled event", evt.event);
  }
}
