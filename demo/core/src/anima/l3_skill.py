"""L3 — Skill Registry.

v0.1: `MockSkillBehaviour` — ticks RUNNING→SUCCESS without doing real work.
v0.2: `SimSkillBehaviour` subclasses drive the MuJoCo sim via the stretch_mujoco
Python API (no ROS, no scripted replay — each run re-queries cup pose and
re-computes arm/base targets analytically).

Skills share a context dict ("blackboard") so locate→navigate→grasp→lift→deliver
can pass targets forward. The context is per-tree (created by
`l2_planner.build_tree`).
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from typing import Awaitable, Callable, Protocol

import mujoco
import py_trees
from py_trees.common import Status

logger = logging.getLogger(__name__)


class StatusCallback(Protocol):
    def __call__(self, node_name: str, status: str) -> Awaitable[None]: ...


# -----------------------------------------------------------------------------
# Mock (v0.1 fallback — used when sim is unavailable)
# -----------------------------------------------------------------------------

class MockSkillBehaviour(py_trees.behaviour.Behaviour):
    def __init__(
        self,
        name: str,
        ticks_to_success: int = 3,
        on_status_change: Callable[[str, str], Awaitable[None]] | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
    ):
        super().__init__(name=name)
        self._ticks_to_success = ticks_to_success
        self._ticks_done = 0
        self._on_status_change = on_status_change
        self._loop = loop

    def initialise(self) -> None:
        self._ticks_done = 0
        self._dispatch("running")

    def update(self) -> Status:
        self._ticks_done += 1
        if self._ticks_done >= self._ticks_to_success:
            self._dispatch("success")
            return Status.SUCCESS
        return Status.RUNNING

    def _dispatch(self, status: str) -> None:
        if not self._on_status_change or not self._loop:
            return
        asyncio.run_coroutine_threadsafe(
            self._on_status_change(self.name, status), self._loop
        )


# -----------------------------------------------------------------------------
# v0.2 sim skills
# -----------------------------------------------------------------------------

# Stretch geometry / scene constants for scene 1 (DRINK_WATER).
ARM_MAX_EXT = 0.52
LIFT_MIN = 0.2
LIFT_MAX = 1.05
APPROACH_Y_OFFSET = 0.60  # base sits this far +Y of cup (arm points -Y)
BASE_POS_TOL = 0.18
BASE_ANGLE_TOL = 0.25
DELIVER_POSE = (2.9, 1.2, -math.pi / 2)


def _read_cup_pose() -> tuple[float, float, float]:
    """Oracle: ground-truth cup position from the MJCF. Closed-world demo;
    perception is out of scope for v0.2."""
    import mujoco

    from src.sim.manager import SCENE_XML

    m = mujoco.MjModel.from_xml_path(SCENE_XML)
    bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "cup")
    if bid < 0:
        return (3.8, 0.8, 0.7)
    return tuple(float(v) for v in m.body_pos[bid])


def _shortest_angle(a: float) -> float:
    return (a + math.pi) % (2 * math.pi) - math.pi


def _drive_toward(sim, goal: tuple[float, float, float], state: dict) -> bool:
    """Unicycle PID: continuously drive toward (gx, gy, gth).

    Two continuous phases: "approach" steers and drives simultaneously until
    within BASE_POS_TOL of (gx, gy); "align" spins in place to reach gth.
    set_base_velocity is sticky across ticks — the server keeps applying the
    last command until a new one arrives, so we only need to update it every
    tick to adapt to drift."""
    gx, gy, gth = goal
    bx, by, bth = sim.get_base_pose()
    dx, dy = gx - bx, gy - by
    dist = math.hypot(dx, dy)
    phase = state.get("phase", "approach")

    if phase == "approach":
        if dist < BASE_POS_TOL:
            sim.set_base_velocity(0.0, 0.0)
            state["phase"] = "align"
            state["align_t0"] = time.time()
            return False
        des_h = math.atan2(dy, dx)
        dh = _shortest_angle(des_h - bth)
        close = dist < 0.6
        # Latch "committed" once we've been within ~2×BASE_POS_TOL of goal:
        # overshoot flips des_h by ~pi which would otherwise trigger a bogus
        # 180° re-align and walk the robot away from the goal.
        if dist < 0.35:
            state["committed"] = True
        committed = state.get("committed", False)
        if not state.get("aligned"):
            align_thresh = 0.30 if close else 0.15
            if abs(dh) > align_thresh:
                w = max(-0.8, min(0.8, 2.0 * dh))
                sim.set_base_velocity(0.0, w)
                return False
            state["aligned"] = True
        lost_thresh = 0.9 if close else 0.5
        if abs(dh) > lost_thresh and not committed:
            state["aligned"] = False
            sim.set_base_velocity(0.0, 0.0)
            return False
        v_floor = 0.12 if committed else (0.2 if close else 0.3)
        v_ceil = 0.4 if committed else 1.0
        v = min(v_ceil, max(v_floor, 1.5 * dist))
        w = max(-0.8, min(0.8, 2.0 * dh))
        sim.set_base_velocity(v, w)
        return False

    # align (final heading)
    dth_f = _shortest_angle(gth - bth)
    if abs(dth_f) < BASE_ANGLE_TOL:
        sim.set_base_velocity(0.0, 0.0)
        return True
    # Timeout: if we've been aligning for too long, accept wider tolerance
    if time.time() - state.get("align_t0", 0.0) > 8.0 and abs(dth_f) < 0.35:
        sim.set_base_velocity(0.0, 0.0)
        return True
    w = 1.2 if dth_f > 0 else -1.2
    sim.set_base_velocity(0.0, w)
    return False


class SimSkillBehaviour(py_trees.behaviour.Behaviour):
    """Base for sim-driven skills. Non-blocking; polled each tick."""

    TIMEOUT_S = 15.0

    def __init__(
        self,
        name: str,
        ctx: dict,
        on_status_change: Callable[[str, str], Awaitable[None]] | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
    ):
        super().__init__(name=name)
        self._ctx = ctx
        self._on_status_change = on_status_change
        self._loop = loop
        self._t_start = 0.0
        self._phase = "init"
        self._start_failed = False

    @property
    def _sim(self):
        from src.sim import get_sim

        return get_sim().sim

    def initialise(self) -> None:
        self._t_start = time.time()
        self._phase = "init"
        self._start_failed = False
        self._dispatch("running")
        try:
            self._start_action()
        except Exception:
            logger.exception("skill %s start failed", self.name)
            self._start_failed = True

    def update(self) -> Status:
        if self._start_failed:
            self._dispatch("fail")
            return Status.FAILURE
        # E-stop preempts any running skill.
        from src.sim import get_sim

        if get_sim().estop_active.is_set():
            try:
                self._sim.set_base_velocity(0.0, 0.0)
            except Exception:
                pass
            self._dispatch("fail")
            return Status.FAILURE
        try:
            done = self._tick()
        except Exception:
            logger.exception("skill %s tick failed", self.name)
            self._dispatch("fail")
            return Status.FAILURE
        if done:
            self._dispatch("success")
            return Status.SUCCESS
        if time.time() - self._t_start > self.TIMEOUT_S:
            logger.warning("skill %s timed out", self.name)
            self._dispatch("fail")
            return Status.FAILURE
        return Status.RUNNING

    def _start_action(self) -> None:  # override
        pass

    def _tick(self) -> bool:  # override, return True when done
        return True

    def _dispatch(self, status: str) -> None:
        if not self._on_status_change or not self._loop:
            return
        asyncio.run_coroutine_threadsafe(
            self._on_status_change(self.name, status), self._loop
        )


class LocateCupSkill(SimSkillBehaviour):
    TIMEOUT_S = 2.0

    def _start_action(self) -> None:
        cx, cy, cz = _read_cup_pose()
        self._ctx["cup_pose"] = (cx, cy, cz)
        self._ctx["base_goal"] = (cx, cy + APPROACH_Y_OFFSET, -math.pi / 2)
        logger.info("cup located at %.2f %.2f %.2f", cx, cy, cz)

    def _tick(self) -> bool:
        return "cup_pose" in self._ctx


class NavigateSkill(SimSkillBehaviour):
    TIMEOUT_S = 90.0

    def _start_action(self) -> None:
        self._drive_state: dict = {}
        self._last_log = 0.0

    def _tick(self) -> bool:
        goal = self._ctx.get("base_goal")
        if not goal:
            return True
        now = time.time()
        if now - self._last_log > 3.0:
            try:
                bx, by, bth = self._sim.get_base_pose()
                logger.info(
                    "nav %s base=(%.2f,%.2f,%.2f) goal=(%.2f,%.2f,%.2f) dist=%.2f phase=%s",
                    self.name, bx, by, bth, *goal,
                    math.hypot(goal[0]-bx, goal[1]-by),
                    self._drive_state.get("phase","?"),
                )
                self._last_log = now
            except Exception:
                pass
        return _drive_toward(self._sim, goal, self._drive_state)


class GraspSkill(SimSkillBehaviour):
    TIMEOUT_S = 20.0

    def _start_action(self) -> None:
        from stretch_mujoco.enums.actuators import Actuators

        sim = self._sim
        cx, cy, cz = self._ctx["cup_pose"]
        bx, by, _ = sim.get_base_pose()
        arm_ext = math.hypot(cx - bx, cy - by) - 0.14
        arm_ext = max(0.05, min(arm_ext, ARM_MAX_EXT))
        lift_z = max(LIFT_MIN, min(LIFT_MAX, cz + 0.02))
        self._ctx["grasp_params"] = (lift_z, arm_ext)

        sim.move_to(Actuators.gripper, 0.5)  # open
        sim.move_to(Actuators.wrist_yaw, 0.0)
        sim.move_to(Actuators.wrist_pitch, 0.0)
        sim.move_to(Actuators.wrist_roll, 0.0)
        sim.move_to(Actuators.lift, lift_z)
        sim.move_to(Actuators.arm, arm_ext)
        self._phase = "reach"

    def _tick(self) -> bool:
        from stretch_mujoco.enums.actuators import Actuators

        sim = self._sim
        if self._phase == "reach":
            if sim.is_reached_set_position(
                Actuators.lift, position_tolerance=0.04
            ) and sim.is_reached_set_position(Actuators.arm, position_tolerance=0.04):
                sim.move_to(Actuators.gripper, -0.4)  # close
                self._phase = "close"
                self._t_phase = time.time()
            return False
        if self._phase == "close":
            return time.time() - self._t_phase > 1.2
        return False


class LiftSkill(SimSkillBehaviour):
    TIMEOUT_S = 8.0

    def _start_action(self) -> None:
        from stretch_mujoco.enums.actuators import Actuators

        sim = self._sim
        lift_z, arm_ext = self._ctx.get("grasp_params", (0.7, 0.3))
        new_lift = min(LIFT_MAX, lift_z + 0.15)
        self._ctx["grasp_params"] = (new_lift, arm_ext)
        sim.move_to(Actuators.lift, new_lift)

    def _tick(self) -> bool:
        from stretch_mujoco.enums.actuators import Actuators

        return self._sim.is_reached_set_position(
            Actuators.lift, position_tolerance=0.04
        )


class DeliverSkill(SimSkillBehaviour):
    """Retract arm, then drive to the bedside, facing the patient."""

    TIMEOUT_S = 60.0

    def _start_action(self) -> None:
        from stretch_mujoco.enums.actuators import Actuators

        sim = self._sim
        sim.move_to(Actuators.arm, 0.08)
        self._phase = "retract"
        self._drive_state: dict = {}

    def _tick(self) -> bool:
        from stretch_mujoco.enums.actuators import Actuators

        sim = self._sim
        if self._phase == "retract":
            if sim.is_reached_set_position(Actuators.arm, position_tolerance=0.08):
                self._phase = "drive"
            return False
        if self._phase == "drive":
            if _drive_toward(sim, DELIVER_POSE, self._drive_state):
                self._phase = "extend"
                sim.move_to(Actuators.arm, 0.25)
            return False
        if self._phase == "extend":
            return sim.is_reached_set_position(Actuators.arm, position_tolerance=0.06)
        return False


class ReleaseSkill(SimSkillBehaviour):
    TIMEOUT_S = 5.0

    def _start_action(self) -> None:
        from stretch_mujoco.enums.actuators import Actuators

        self._sim.move_to(Actuators.gripper, 0.5)
        self._t_phase = time.time()

    def _tick(self) -> bool:
        return time.time() - self._t_phase > 0.8


# -----------------------------------------------------------------------------
# v0.3 extra skills: goto bed, toggle light, toggle TV, call caregiver.
# -----------------------------------------------------------------------------

BEDSIDE_POSE = (4.5, 1.3, -math.pi / 2)
# Head-side-of-bed pose. User feedback was 「去床边可以绕到床边人头位置」, so we
# drive past the bed (patient head ~ x=4.5, bed body at x=3.8) and stop facing
# the head end. y=1.3 is necessary — the nightstand collision box at (3.8, 0.65)
# extends to y=0.79, and the Stretch footprint radius ~0.35m means any goal
# with y<1.15 deadlocks the unicycle PID against the nightstand (oscillates in
# place at x~3.7). Earlier v0.3 used (2.71, 1.25) which parked at the foot.


class GotoBedSkill(SimSkillBehaviour):
    """Drive base to the bedside pose, no manipulation."""

    TIMEOUT_S = 60.0

    def _start_action(self) -> None:
        self._drive_state: dict = {}

    def _tick(self) -> bool:
        return _drive_toward(self._sim, BEDSIDE_POSE, self._drive_state)


class ToggleLightSkill(SimSkillBehaviour):
    """Set room lights to a specific state derived from the subtask name.

    Why not a pure toggle: a pure toggle violates user intent — saying "关灯"
    twice flips the lights back ON, which is confusing when the front-end shows
    a "关灯" button. Instead, the canonical plans bind TURN_OFF_LIGHT to subtask
    name "turn_off_light" and TURN_ON_LIGHT to "turn_on_light"; we read that
    name here so each intent is idempotent."""

    TIMEOUT_S = 3.0

    def _start_action(self) -> None:
        from src.sim import get_sim

        mgr = get_sim()
        self._mgr = mgr
        if self.name == "turn_off_light":
            target_on = False
        elif self.name == "turn_on_light":
            target_on = True
        else:
            target_on = bool(getattr(mgr, "_light_off", False))  # legacy toggle fallback
        mgr.set_lights_on(target_on)
        self._t_phase = time.time()

    def _tick(self) -> bool:
        return time.time() - self._t_phase > 0.4


class ToggleDeviceSkill(SimSkillBehaviour):
    """Flip the TV screen between dark-off and bright-on."""

    TIMEOUT_S = 3.0

    def _start_action(self) -> None:
        from src.sim import get_sim

        mgr = get_sim()
        on = not getattr(mgr, "_tv_on", False)
        mgr.set_tv_on(on)
        self._t_phase = time.time()

    def _tick(self) -> bool:
        return time.time() - self._t_phase > 0.4


# Nurse mocap waypoints. Hidden state z=-10 keeps her out of every camera
# (including top_down). _NURSE_INSIDE is right next to the visitor_chair so
# demo_view sees her clearly.
_NURSE_HIDDEN = (-3.0, 1.0, -10.0)
_NURSE_INSIDE = (1.0, 1.5, 0.0)
# Yaw turns the face (+X side of the geom layout) toward demo_view at ~+X,-Y.
_NURSE_FACE_YAW = -math.pi / 4


class CallHelpSkill(SimSkillBehaviour):
    """Raise lift as a beacon AND have the nurse appear bedside for a beat.

    Software-rendering osmesa at 5x540p only achieves ~0.4 fps under load, so a
    slid "walk-in" only renders 1-2 frames and just looks like a teleport.
    Instead we teleport her directly to the bedside, hold her there long enough
    for the slow renderer to emit several frames showing her present, then
    teleport her back under the floor."""

    TIMEOUT_S = 9.0
    _HOLD_S = 6.0  # >> render period, so multiple frames catch her in-room

    def _start_action(self) -> None:
        from stretch_mujoco.enums.actuators import Actuators
        from src.sim import get_sim

        # Robot side: raise lift as the "I heard you" beacon.
        self._sim.move_to(Actuators.lift, 0.95)
        self._sim.move_to(Actuators.arm, 0.1)

        # Nurse side: cache mocap index, then teleport her into the room.
        self._mgr = get_sim()
        self._nurse_idx = -1
        m = getattr(self._mgr, "_model", None)
        d = getattr(self._mgr, "_data", None)
        if m is not None and d is not None:
            try:
                bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "nurse")
                if bid >= 0:
                    self._nurse_idx = int(m.body_mocapid[bid])
            except Exception:
                self._nurse_idx = -1
        self._set_nurse_pose(_NURSE_INSIDE, yaw=_NURSE_FACE_YAW)
        self._t_phase = time.time()

    def _set_nurse_pose(self, xyz, yaw: float = 0.0) -> None:
        d = self._mgr._data
        if d is None or self._nurse_idx < 0:
            return
        d.mocap_pos[self._nurse_idx] = xyz
        d.mocap_quat[self._nurse_idx] = (
            math.cos(yaw / 2.0),
            0.0,
            0.0,
            math.sin(yaw / 2.0),
        )

    def _tick(self) -> bool:
        if time.time() - self._t_phase < self._HOLD_S:
            return False
        self._set_nurse_pose(_NURSE_HIDDEN, yaw=0.0)
        return True


SKILL_REGISTRY: dict[str, type[SimSkillBehaviour]] = {
    "locate": LocateCupSkill,
    "navigate": NavigateSkill,
    "grasp": GraspSkill,
    "lift": LiftSkill,
    "deliver": DeliverSkill,
    "release": ReleaseSkill,
    "goto_bed": GotoBedSkill,
    "toggle_light": ToggleLightSkill,
    "toggle_device": ToggleDeviceSkill,
    "call_help": CallHelpSkill,
}
