"""SimManager — owns the single StretchMujocoSimulator + renders `demo_view`.

stretch_mujoco's `pull_camera_data()` only returns frames from the 5 on-robot
cameras (d405/d435i/nav). To expose the third-person `demo_view` camera we
build a parallel `mujoco.MjModel` in the main process and sync robot joint
positions from `sim.pull_status()` each frame, then render with
`mujoco.Renderer`.

The render only needs to be visually correct, not physically authoritative —
the sim subprocess is the source of truth for physics and skill execution.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import cv2
    import mujoco
    import numpy as np
    from stretch_mujoco import StretchMujocoSimulator

    _DEPS_OK = True
except Exception as exc:  # noqa: BLE001
    logger.warning("SimManager deps unavailable: %s", exc)
    _DEPS_OK = False


SCENE_XML = os.environ.get(
    "ANIMA_SCENE_XML",
    "/root/pkgs/stretch_mujoco/stretch_mujoco/models/hospital_ward.xml",
)
STREAM_CAMERAS = ("demo_view", "grasp_view", "bedside_view", "top_down", "tv_view")
DEFAULT_CAMERA = "demo_view"
JPEG_QUALITY = 70
TARGET_FPS = 15
RENDER_W = 640
RENDER_H = 360
START_TRANSLATION = [2.2, 1.25, 0.0]


class _CameraFeed:
    """Per-camera renderer + latest JPEG. The render loop ticks all feeds
    from a single scene sync — each feed has its own Renderer but shares
    the same MjData."""

    def __init__(self, name: str, model, w: int, h: int) -> None:
        self.name = name
        self.renderer = mujoco.Renderer(model, height=h, width=w)
        self.renderer._scene_option.flags[mujoco.mjtVisFlag.mjVIS_RANGEFINDER] = False
        self.latest_jpeg: bytes | None = None
        self.cond = threading.Condition()


class SimManager:
    def __init__(self) -> None:
        self.available = _DEPS_OK and Path(SCENE_XML).exists()
        self._sim = None
        self._model = None
        self._data = None
        self._feeds: dict[str, _CameraFeed] = {}
        self._qaddr = {}
        self._render_thread: threading.Thread | None = None
        self._stop_flag = threading.Event()
        # Device states — tracked so skills can alternate on/off across calls.
        self._light_off: bool = False
        self._tv_on: bool = False
        self._light_diffuse_orig = None
        self._light_mat_emission_orig = None
        self._tv_screen_geom_id: int = -1
        # E-stop: set to True to abort any in-flight BT skill tick.
        self.estop_active: threading.Event = threading.Event()

    # ---------------- lifecycle -----------------

    def start(self) -> None:
        if not self.available:
            logger.info("SimManager.start skipped (deps/scene missing)")
            return
        if self._sim is not None:
            return
        logger.info("Starting StretchMujocoSimulator scene=%s", SCENE_XML)
        self._sim = StretchMujocoSimulator(
            scene_xml_path=SCENE_XML,
            cameras_to_use=[],
            camera_hz=TARGET_FPS,
            start_translation=START_TRANSLATION,
        )
        self._sim.start(headless=True)
        if not self._sim.is_running():
            logger.error("Sim process failed to start (check scene xml)")
            self._sim = None
            return

        self._model = mujoco.MjModel.from_xml_path(SCENE_XML)
        self._data = mujoco.MjData(self._model)
        # One renderer per advertised camera — allows PiP / parallel streams
        # without re-aiming a single GL context across clients.
        self._feeds = {}
        for cam in STREAM_CAMERAS:
            if mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_CAMERA, cam) < 0:
                logger.warning("camera %s not in scene, skipping", cam)
                continue
            self._feeds[cam] = _CameraFeed(cam, self._model, RENDER_W, RENDER_H)
        self._build_qaddr()

        self._stop_flag.clear()
        self._render_thread = threading.Thread(
            target=self._render_loop, name="sim-render", daemon=True
        )
        self._render_thread.start()

    def stop(self) -> None:
        # Order matters: the render loop holds mujoco.Renderer objects that
        # dereference `_model` on every tick. If we null `_model` while the
        # render thread is mid-frame the process segfaults. So:
        #   1. flag render thread to stop and wait generously (up to 10s)
        #   2. only then release renderers and the model
        self._stop_flag.set()
        if self._render_thread:
            self._render_thread.join(timeout=10.0)
            if self._render_thread.is_alive():
                logger.error("render thread refused to stop — leaving renderers alive")
            self._render_thread = None
        # Explicitly release renderer GL contexts before dropping model refs.
        for feed in self._feeds.values():
            try:
                feed.renderer.close()
            except Exception:
                pass
        self._feeds = {}
        if self._sim is not None:
            try:
                self._sim.stop()
            except Exception as exc:  # noqa: BLE001
                logger.warning("sim.stop failed: %s", exc)
            self._sim = None
        self._model = None
        self._data = None
        # Device state caches belong to a specific model instance.
        self._light_diffuse_orig = None
        self._light_mat_emission_orig = None
        self._tv_screen_geom_id = -1
        self._light_off = False
        self._tv_on = False
        self.estop_active.clear()

    def reset(self) -> None:
        if not self.available:
            return
        self.stop()
        self.start()

    # ---------------- accessors -----------------

    @property
    def sim(self):
        return self._sim

    def cameras(self) -> list[str]:
        return list(self._feeds.keys())

    def _resolve_feed(self, camera: str | None) -> _CameraFeed | None:
        if not self._feeds:
            return None
        if camera and camera in self._feeds:
            return self._feeds[camera]
        return self._feeds.get(DEFAULT_CAMERA) or next(iter(self._feeds.values()))

    def wait_next_frame(self, timeout: float = 2.0, camera: str | None = None) -> bytes | None:
        feed = self._resolve_feed(camera)
        if feed is None:
            return None
        with feed.cond:
            feed.cond.wait(timeout=timeout)
            return feed.latest_jpeg

    def latest_frame(self, camera: str | None = None) -> bytes | None:
        feed = self._resolve_feed(camera)
        if feed is None:
            return None
        with feed.cond:
            return feed.latest_jpeg

    # ---------------- device toggles & diag -----------------

    def cup_pose(self) -> tuple[float, float, float] | None:
        """Live cup position from the sim subprocess (via get_link_pose, which
        resolves any named body in the MJCF, not just robot links)."""
        if self._sim is None:
            return None
        try:
            pose = self._sim.get_link_pose("cup")
            return (float(pose[0]), float(pose[1]), float(pose[2]))
        except Exception:
            return None

    def set_lights_on(self, on: bool) -> None:
        """Zero all light diffuses (and the ceiling-light material emission)
        when off; restore when on."""
        if self._model is None:
            return
        if self._light_diffuse_orig is None:
            self._light_diffuse_orig = self._model.light_diffuse.copy()
            try:
                self._light_mat_emission_orig = self._model.mat_emission.copy()
            except Exception:
                self._light_mat_emission_orig = None
        if on:
            self._model.light_diffuse[:] = self._light_diffuse_orig
            if self._light_mat_emission_orig is not None:
                self._model.mat_emission[:] = self._light_mat_emission_orig
        else:
            self._model.light_diffuse[:] = 0.0
            if self._light_mat_emission_orig is not None:
                self._model.mat_emission[:] = 0.0
        self._light_off = not on

    def set_tv_on(self, on: bool) -> None:
        if self._model is None:
            return
        import mujoco

        if self._tv_screen_geom_id < 0:
            self._tv_screen_geom_id = mujoco.mj_name2id(
                self._model, mujoco.mjtObj.mjOBJ_GEOM, "tv_screen"
            )
        gid = self._tv_screen_geom_id
        if gid < 0:
            return
        if on:
            self._model.geom_rgba[gid] = (0.35, 0.75, 1.0, 1.0)
        else:
            self._model.geom_rgba[gid] = (0.05, 0.05, 0.08, 1.0)
        self._tv_on = on

    def trigger_estop(self) -> None:
        """Abort current skill execution and zero out the robot's motion.
        Skills check this flag each tick and raise to fail the BT."""
        self.estop_active.set()
        if self._sim is None:
            return
        try:
            self._sim.set_base_velocity(0.0, 0.0)
        except Exception:
            pass

    def clear_estop(self) -> None:
        self.estop_active.clear()

    # ---------------- internals -----------------

    def _build_qaddr(self) -> None:
        m = self._model
        self._qaddr = {}
        name_to_joint = [
            "joint_lift",
            "joint_arm_l0",
            "joint_arm_l1",
            "joint_arm_l2",
            "joint_arm_l3",
            "joint_wrist_yaw",
            "joint_wrist_pitch",
            "joint_wrist_roll",
            "joint_head_pan",
            "joint_head_tilt",
        ]
        for n in name_to_joint:
            jid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)
            if jid >= 0:
                self._qaddr[n] = m.jnt_qposadr[jid]
        # base freejoint is joint 0 (7 qpos: xyz + quat)
        self._qaddr["base"] = m.jnt_qposadr[0]

    def _sync_state(self) -> None:
        """Copy the robot's state from sim subprocess into main-process qpos."""
        status = self._sim.pull_status()
        b = status.base
        qa = self._qaddr["base"]
        # base freejoint: x, y, z, qw, qx, qy, qz
        import math

        half = b.theta / 2.0
        qw, qz = math.cos(half), math.sin(half)
        self._data.qpos[qa : qa + 7] = [b.x, b.y, 0.0, qw, 0.0, 0.0, qz]

        self._data.qpos[self._qaddr["joint_lift"]] = status.lift.pos
        # arm telescope: total extension split across 4 segments
        seg = status.arm.pos / 4.0
        for n in (
            "joint_arm_l0",
            "joint_arm_l1",
            "joint_arm_l2",
            "joint_arm_l3",
        ):
            self._data.qpos[self._qaddr[n]] = seg
        self._data.qpos[self._qaddr["joint_wrist_yaw"]] = status.wrist_yaw.pos
        self._data.qpos[self._qaddr["joint_wrist_pitch"]] = status.wrist_pitch.pos
        self._data.qpos[self._qaddr["joint_wrist_roll"]] = status.wrist_roll.pos
        self._data.qpos[self._qaddr["joint_head_pan"]] = status.head_pan.pos
        self._data.qpos[self._qaddr["joint_head_tilt"]] = status.head_tilt.pos

        mujoco.mj_forward(self._model, self._data)

    def _render_loop(self) -> None:
        assert self._sim is not None and self._feeds
        period = 1.0 / TARGET_FPS
        while not self._stop_flag.is_set():
            # Re-check shutdown flag at each tick AND bail early if resources
            # have been released out from under us (defensive — stop() owns
            # the shutdown ordering but we still want to guard against races).
            if self._model is None or self._data is None or not self._feeds:
                break
            t0 = time.perf_counter()
            try:
                if not self._sim.is_running():
                    time.sleep(0.2)
                    continue
                self._sync_state()
                for feed in self._feeds.values():
                    feed.renderer.update_scene(self._data, camera=feed.name)
                    rgb = feed.renderer.render()
                    jpeg = self._encode(rgb)
                    if jpeg:
                        with feed.cond:
                            feed.latest_jpeg = jpeg
                            feed.cond.notify_all()
            except Exception as exc:  # noqa: BLE001
                logger.warning("render loop error: %s", exc)
                time.sleep(0.2)
            dt = time.perf_counter() - t0
            if dt < period:
                time.sleep(period - dt)

    @staticmethod
    def _encode(rgb: "np.ndarray") -> bytes:
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        ok, buf = cv2.imencode(
            ".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
        )
        return buf.tobytes() if ok else b""


_sim_manager = SimManager()


def get_sim() -> SimManager:
    return _sim_manager
