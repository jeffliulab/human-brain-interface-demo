"use client";

import { useState, useCallback, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8765";

const CAMERA_LABELS: Record<string, string> = {
  demo_view: "总览",
  grasp_view: "抓取特写",
  bedside_view: "床边视角",
  top_down: "俯视",
  tv_view: "电视视角",
};

export function SimulationView() {
  const [resetting, setResetting] = useState(false);
  const [streamKey, setStreamKey] = useState(0);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [cameras, setCameras] = useState<string[]>([]);
  const [camera, setCamera] = useState<string>("demo_view");
  const [estop, setEstop] = useState(false);

  // Poll sim status every 3s so the UI auto-recovers when the backend
  // restarts (e.g., after a Reset Sim that triggers a sim-subprocess cycle,
  // or if the API service itself was restarted by systemd).
  useEffect(() => {
    let cancelled = false;
    const check = () => {
      fetch(`${API_URL}/api/sim/status`)
        .then((r) => r.json())
        .then((j) => {
          if (cancelled) return;
          setAvailable(Boolean(j?.available && j?.running));
        })
        .catch(() => !cancelled && setAvailable(false));
    };
    check();
    const iv = setInterval(check, 3000);
    return () => {
      cancelled = true;
      clearInterval(iv);
    };
  }, []);

  useEffect(() => {
    if (available !== true) return;
    fetch(`${API_URL}/api/sim/cameras`)
      .then((r) => r.json())
      .then((j) => {
        const list = Array.isArray(j?.cameras) ? j.cameras : [];
        setCameras(list);
        if (list.length && !list.includes(camera)) {
          setCamera(list[0]);
        }
      })
      .catch(() => setCameras([]));
    // camera only seeds; list-fetch should not refire on camera change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [available]);

  const handleReset = useCallback(async () => {
    setResetting(true);
    setAvailable(null);  // re-enter "checking" state; status poll will flip
                         // back to true once the sim subprocess comes back.
    try {
      await fetch(`${API_URL}/api/sim/reset`, { method: "POST" });
      // Sim restart takes ~15s; delay the <img> refresh until the stream
      // is actually reachable again.
      setTimeout(() => setStreamKey((k) => k + 1), 17000);
      setEstop(false);
    } catch (err) {
      console.error("sim reset failed", err);
    } finally {
      setTimeout(() => setResetting(false), 18000);
    }
  }, []);

  const handleEstop = useCallback(async () => {
    try {
      await fetch(`${API_URL}/api/sim/estop`, { method: "POST" });
      setEstop(true);
    } catch (err) {
      console.error("estop failed", err);
    }
  }, []);

  const handleClearEstop = useCallback(async () => {
    try {
      await fetch(`${API_URL}/api/sim/estop/clear`, { method: "POST" });
      setEstop(false);
    } catch (err) {
      console.error("clear estop failed", err);
    }
  }, []);

  const switchCamera = useCallback((name: string) => {
    setCamera(name);
    setStreamKey((k) => k + 1);
  }, []);

  const streamSrc = `${API_URL}/api/sim/mjpeg?camera=${encodeURIComponent(
    camera,
  )}&t=${streamKey}`;

  return (
    <section className="flex h-full w-full flex-col overflow-hidden rounded-xl border border-zinc-200 bg-zinc-50/40">
      <header className="flex shrink-0 items-center justify-between border-b border-zinc-200 px-4 py-2">
        <div>
          <h2 className="text-sm font-semibold text-zinc-100">MuJoCo Live View</h2>
          <p className="text-[10px] text-zinc-500">
            {CAMERA_LABELS[camera] ?? camera} · Stretch RE3 · hospital ward
          </p>
        </div>
        <div className="flex items-center gap-2">
          {estop ? (
            <button
              type="button"
              onClick={handleClearEstop}
              disabled={available === false}
              className="rounded-md bg-amber-500 px-3 py-1 text-xs font-semibold text-white hover:bg-amber-400 disabled:opacity-40"
            >
              Clear E-stop
            </button>
          ) : (
            <button
              type="button"
              onClick={handleEstop}
              disabled={available === false}
              className="rounded-md bg-rose-600 px-3 py-1 text-xs font-semibold text-white hover:bg-rose-500 disabled:opacity-40"
              title="紧急停止 — 立即抢占并中止当前行为树，旁路 Anima 管线"
            >
              E-stop
            </button>
          )}
          <button
            type="button"
            onClick={handleReset}
            disabled={resetting || available === false}
            className="rounded-md bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-900 hover:bg-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            {resetting ? "Resetting…" : "Reset Sim"}
          </button>
        </div>
      </header>
      {estop && (
        <div className="flex shrink-0 items-center gap-2 border-b border-rose-300 bg-rose-100/80 px-3 py-1.5 text-[11px] font-medium text-rose-800">
          <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-rose-600" />
          E-stop active — BT preempted. Click Clear E-stop to resume.
        </div>
      )}
      {cameras.length > 1 && (
        <div className="flex shrink-0 gap-1 border-b border-zinc-200 bg-white/60 px-2 py-1.5">
          {cameras.map((name) => {
            const active = name === camera;
            return (
              <button
                key={name}
                type="button"
                onClick={() => switchCamera(name)}
                className={
                  "rounded-md px-2.5 py-1 text-[11px] font-medium transition " +
                  (active
                    ? "bg-zinc-900 text-white"
                    : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200")
                }
              >
                {CAMERA_LABELS[name] ?? name}
              </button>
            );
          })}
        </div>
      )}
      <div className="relative min-h-0 flex-1 w-full overflow-hidden bg-white">
        {available === false ? (
          <div className="flex h-full items-center justify-center text-xs text-zinc-500">
            Sim backend unavailable — run FastAPI on a host with MuJoCo.
          </div>
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            key={`${camera}-${streamKey}`}
            src={streamSrc}
            alt={`MuJoCo ${camera} stream`}
            className="h-full w-full object-contain"
          />
        )}
      </div>
    </section>
  );
}
