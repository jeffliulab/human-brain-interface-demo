"use client";

import { useEffect, useRef, useState } from "react";
import { useDemoStore } from "@/lib/store";

const CH_LABELS = Array.from({ length: 16 }, (_, i) =>
  `M1-L_${(i + 1).toString().padStart(2, "0")}`
);

export function NeuralActivity() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const waveform = useDemoStore((s) => s.waveform);
  const [mode, setMode] = useState<"raster" | "wave">("raster");

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const { width, height } = canvas.getBoundingClientRect();
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const nCh = 16;
    const labelW = 54;
    const plotX = labelW;
    const plotW = width - labelW - 4;
    const rowH = height / nCh;

    for (let i = 0; i < nCh; i++) {
      if (i % 2 === 0) {
        ctx.fillStyle = "rgba(63, 63, 70, 0.25)";
        ctx.fillRect(plotX, i * rowH, plotW, rowH);
      }
      ctx.fillStyle = "#71717a";
      ctx.font = "9px ui-monospace";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(CH_LABELS[i], 2, i * rowH + rowH / 2);
    }

    if (!waveform) {
      ctx.fillStyle = "#52525b";
      ctx.font = "10px ui-monospace";
      ctx.textAlign = "center";
      ctx.fillText(
        "awaiting intent — no neural stream",
        plotX + plotW / 2,
        height / 2
      );
      return;
    }

    const channels = waveform.channels.slice(0, nCh);

    if (mode === "wave") {
      channels.forEach((frames, i) => {
        const y0 = rowH * i + rowH / 2;
        ctx.strokeStyle = "#e4e4e7";
        ctx.lineWidth = 0.8;
        ctx.globalAlpha = 0.9;
        ctx.beginPath();
        frames.forEach((v, j) => {
          const x = plotX + (j / (frames.length - 1)) * plotW;
          const y = y0 - v * rowH * 0.42;
          if (j === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.stroke();
      });
      ctx.globalAlpha = 1;
    } else {
      ctx.fillStyle = "#7dd3fc";
      ctx.globalAlpha = 0.85;
      channels.forEach((frames, i) => {
        const y0 = rowH * i + rowH / 2;
        const n = frames.length;
        for (let j = 0; j < n; j++) {
          if (Math.abs(frames[j]) > 0.55) {
            const x = plotX + (j / (n - 1)) * plotW;
            ctx.fillRect(x - 0.5, y0 - 2, 1, 4);
          }
        }
      });
      ctx.globalAlpha = 1;
    }
  }, [waveform, mode]);

  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-3">
      <div className="flex items-center justify-between">
        <label className="text-xs uppercase tracking-wide text-zinc-600">
          Neural Activity
        </label>
        <div className="flex overflow-hidden rounded border border-zinc-300 text-[10px]">
          <button
            onClick={() => setMode("raster")}
            className={`px-2 py-0.5 ${
              mode === "raster"
                ? "bg-sky-900/60 text-sky-200"
                : "text-zinc-600 hover:text-zinc-800"
            }`}
          >
            raster
          </button>
          <button
            onClick={() => setMode("wave")}
            className={`border-l border-zinc-300 px-2 py-0.5 ${
              mode === "wave"
                ? "bg-sky-900/60 text-sky-200"
                : "text-zinc-600 hover:text-zinc-800"
            }`}
          >
            µV
          </button>
        </div>
      </div>
      <canvas ref={canvasRef} className="mt-2 h-48 w-full rounded bg-zinc-100/50" />
      <div className="mt-1 flex justify-between text-[9px] text-zinc-600">
        <span>16 ch · 4 s window</span>
        <span>{mode === "raster" ? "threshold · 3σ" : "±100 µV"}</span>
      </div>
    </div>
  );
}
