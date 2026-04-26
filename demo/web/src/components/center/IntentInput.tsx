"use client";

import { useEffect, useState, useTransition } from "react";
import { submitIntent } from "@/lib/api";
import { useDemoStore } from "@/lib/store";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8765";

export function IntentInput() {
  const [text, setText] = useState("");
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [lightOff, setLightOff] = useState(false);
  const reset = useDemoStore((s) => s.reset);

  // Poll sim status so the light convenience button can flip its label
  // between "关灯" (when lights are on) and "开灯" (when lights are off).
  useEffect(() => {
    let cancelled = false;
    const poll = () =>
      fetch(`${API_URL}/api/sim/status`)
        .then((r) => r.json())
        .then((j) => !cancelled && setLightOff(Boolean(j?.light_off)))
        .catch(() => {});
    poll();
    const iv = setInterval(poll, 3000);
    return () => {
      cancelled = true;
      clearInterval(iv);
    };
  }, []);

  const examples = [
    "我想喝水",
    "打开电视",
    "叫护士过来",
    "去床边",
    lightOff ? "开灯" : "关灯",
  ];

  const send = (value: string) => {
    if (!value.trim() || isPending) return;
    setError(null);
    reset();
    startTransition(async () => {
      try {
        await submitIntent(value);
        setText("");
      } catch (e) {
        setError(e instanceof Error ? e.message : "request failed");
      }
    });
  };

  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-4">
      <label className="text-xs uppercase tracking-wide text-zinc-600">
        L0 · Intent Input
      </label>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
            e.preventDefault();
            send(text);
          }
        }}
        placeholder="输入自然语言指令，例如：我想喝水"
        rows={3}
        className="mt-2 w-full resize-none rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-500 focus:border-sky-500 focus:outline-none"
      />
      <div className="mt-2 flex items-center justify-between gap-2">
        <div className="flex flex-wrap gap-1">
          {examples.map((ex) => (
            <button
              key={ex}
              onClick={() => send(ex)}
              disabled={isPending}
              className="rounded border border-zinc-300 bg-zinc-50 px-2 py-1 text-xs text-zinc-600 hover:border-sky-600 hover:text-sky-700 disabled:opacity-40"
            >
              {ex}
            </button>
          ))}
        </div>
        <button
          onClick={() => send(text)}
          disabled={isPending || !text.trim()}
          className="rounded-md bg-sky-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-sky-500 disabled:bg-zinc-300 disabled:text-zinc-600"
        >
          {isPending ? "运行中…" : "发送 (⌘↵)"}
        </button>
      </div>
      {error && <p className="mt-2 text-xs text-rose-700">{error}</p>}
    </div>
  );
}
