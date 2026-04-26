"""Simulation HTTP routes — MJPEG stream + reset."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.routes.ws import manager as ws_manager
from src.sim import get_sim

logger = logging.getLogger(__name__)

router = APIRouter()


async def _mjpeg_generator(camera: str | None):
    sim = get_sim()
    boundary = b"--frame"
    while True:
        jpeg = await asyncio.to_thread(sim.wait_next_frame, 2.0, camera)
        if not jpeg:
            await asyncio.sleep(0.1)
            continue
        yield (
            boundary
            + b"\r\nContent-Type: image/jpeg\r\nContent-Length: "
            + str(len(jpeg)).encode()
            + b"\r\n\r\n"
            + jpeg
            + b"\r\n"
        )


@router.get("/api/sim/cameras")
async def list_cameras():
    sim = get_sim()
    if not sim.available:
        raise HTTPException(status_code=503, detail="sim unavailable")
    return {"cameras": sim.cameras()}


@router.get("/api/sim/mjpeg")
async def mjpeg_stream(camera: str | None = None):
    sim = get_sim()
    if not sim.available:
        raise HTTPException(status_code=503, detail="sim unavailable")
    if camera and camera not in sim.cameras():
        raise HTTPException(status_code=404, detail=f"unknown camera {camera}")
    return StreamingResponse(
        _mjpeg_generator(camera),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.post("/api/sim/reset")
async def reset_sim():
    sim = get_sim()
    if not sim.available:
        raise HTTPException(status_code=503, detail="sim unavailable")
    await asyncio.to_thread(sim.reset)
    sim.clear_estop()
    return {"ok": True}


@router.post("/api/sim/estop")
async def estop_sim():
    """Emergency stop — preempt any running BT skill and zero the base.
    Broadcasts an `estop.active` ws event so the UI can reflect the state
    without waiting for the BT tick to fail-dispatch through on_status_change."""
    sim = get_sim()
    if not sim.available:
        raise HTTPException(status_code=503, detail="sim unavailable")
    await asyncio.to_thread(sim.trigger_estop)
    await ws_manager.broadcast("estop.active", {"ts": None})
    return {"ok": True}


@router.post("/api/sim/estop/clear")
async def clear_estop():
    sim = get_sim()
    if not sim.available:
        raise HTTPException(status_code=503, detail="sim unavailable")
    sim.clear_estop()
    await ws_manager.broadcast("estop.cleared", {})
    return {"ok": True}


@router.get("/api/sim/status")
async def sim_status():
    sim = get_sim()
    return {
        "available": sim.available,
        "running": sim.sim is not None,
        "estop": sim.estop_active.is_set() if sim.available else False,
        "light_off": getattr(sim, "_light_off", False),
        "tv_on": getattr(sim, "_tv_on", False),
    }


@router.get("/api/sim/diag")
async def sim_diag():
    """Snapshot of robot + cup state, for debugging skill timeouts."""
    mgr = get_sim()
    if not mgr.available or mgr.sim is None:
        raise HTTPException(status_code=503, detail="sim unavailable")
    s = mgr.sim
    try:
        bx, by, bth = s.get_base_pose()
        status = s.pull_status()
        out = {
            "base": {"x": float(bx), "y": float(by), "theta": float(bth)},
            "lift": float(status.lift.pos),
            "arm": float(status.arm.pos),
            "gripper": float(status.gripper.pos),
        }
        cup = mgr.cup_pose()
        if cup is not None:
            out["cup_body_pos"] = list(cup)
        out["light_off"] = getattr(mgr, "_light_off", False)
        out["tv_on"] = getattr(mgr, "_tv_on", False)
        return out
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
