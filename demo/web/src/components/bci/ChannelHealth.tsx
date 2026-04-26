"use client";

import { useDemoStore } from "@/lib/store";

function Ring({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="flex flex-col items-center">
      <div
        className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${color}`}
      >
        <span className="font-mono text-[10px] text-zinc-900">{value}</span>
      </div>
      <span className="mt-1 text-[9px] uppercase tracking-wide text-zinc-500">
        {label}
      </span>
    </div>
  );
}

export function ChannelHealth() {
  const waveform = useDemoStore((s) => s.waveform);
  const channels = waveform?.channels?.length ?? 0;
  const total = 16;
  const good = Math.min(channels || 0, total);

  const yieldColor =
    good === 0
      ? "border-zinc-300 text-zinc-600"
      : good >= 14
      ? "border-emerald-500"
      : good >= 10
      ? "border-amber-500"
      : "border-rose-500";

  const snr = channels > 0 ? 22 : 0;
  const snrColor = snr >= 20 ? "border-emerald-500" : snr >= 10 ? "border-amber-500" : "border-rose-500";

  const cqText = channels > 0 ? "12·3·1·0" : "—·—·—·—";
  const artifact = channels === 0 ? "—" : "0";
  const artColor = artifact === "0" ? "border-emerald-500" : "border-rose-500";

  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50/50 p-3">
      <div className="flex items-center justify-between">
        <label className="text-xs uppercase tracking-wide text-zinc-600">
          Channel Health
        </label>
        <span className="text-[9px] font-mono text-zinc-600">Utah-array · M1-L</span>
      </div>
      <div className="mt-2 grid grid-cols-4 gap-2">
        <Ring label="yield" value={`${good}/${total}`} color={yieldColor} />
        <Ring label="cq g·o·r·b" value={cqText} color="border-zinc-600" />
        <Ring label="snr dB" value={snr > 0 ? `${snr}` : "—"} color={snrColor} />
        <Ring label="artifact" value={artifact} color={artColor} />
      </div>
    </div>
  );
}
