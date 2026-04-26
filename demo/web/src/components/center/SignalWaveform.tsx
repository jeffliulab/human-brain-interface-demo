"use client";

import { useEffect, useRef } from "react";
import { useDemoStore } from "@/lib/store";

const CH_COLORS = [
  "#38bdf8", "#22d3ee", "#67e8f9", "#a5f3fc",
  "#bae6fd", "#7dd3fc", "#38bdf8", "#0ea5e9",
  "#0284c7", "#0369a1", "#075985", "#0c4a6e",
  "#60a5fa", "#3b82f6", "#2563eb", "#1d4ed8",
];

export function SignalWaveform() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const waveform = useDemoStore((s) => s.waveform);

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

    if (!waveform) {
      ctx.fillStyle = "#52525b";
      ctx.font = "11px ui-monospace";
      ctx.textAlign = "center";
      ctx.fillText("no signal — submit an intent to generate waveform", width / 2, height / 2);
      return;
    }

    const channels = waveform.channels.slice(0, 16);
    const nCh = channels.length;
    const rowH = height / nCh;

    channels.forEach((frames, i) => {
      const y0 = rowH * i + rowH / 2;
      ctx.strokeStyle = CH_COLORS[i % CH_COLORS.length];
      ctx.lineWidth = 1;
      ctx.globalAlpha = 0.85;
      ctx.beginPath();
      frames.forEach((v, j) => {
        const x = (j / (frames.length - 1)) * width;
        const y = y0 - v * rowH * 0.4;
        if (j === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    });
    ctx.globalAlpha = 1;
  }, [waveform]);

  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-4">
      <div className="flex items-center justify-between">
        <label className="text-xs uppercase tracking-wide text-zinc-600">
          Decorative Signal (16 / 256 ch)
        </label>
        <span className="text-[10px] text-zinc-600">
          text-hash seeded · not neural data
        </span>
      </div>
      <canvas
        ref={canvasRef}
        className="mt-2 h-40 w-full rounded bg-zinc-100/40"
      />
    </div>
  );
}
