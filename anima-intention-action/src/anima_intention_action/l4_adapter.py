"""L4 — Embodied Adapter (renamed from Anima's original "Policy" layer).

The BCI adaptation is device-agnostic by design: the same L1-L3 stack
targets wheelchairs, manipulators, quadrupeds, and future humanoids.
L4's job is to take the L3 skill's desired effect (e.g. "drive to pose",
"grasp cup at xyz") and translate it for whichever device is active.

An adapter declares its *capabilities* at registration time; L1 / L2 use
the capability list plus affordance scoring to route subtasks to the
right device. An adapter is also the owner of the non-BCI E-stop
channels (physical button, voice keyword, eye-closure) — see doc 06.

This module ships a minimal protocol plus a ``MockAdapter`` for tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class AdapterCapabilities:
    """Declared at registration; used by L1/L2 for affordance scoring."""

    name: str
    mobile_base: bool = False
    manipulator: bool = False
    gripper: bool = False
    max_payload_kg: float = 0.0
    workspace_reach_m: float = 0.0
    tags: tuple[str, ...] = field(default_factory=tuple)


class EmbodiedAdapter(Protocol):
    """Minimal shape every adapter must implement.

    Real adapters (Stretch, wheelchair, Spot, humanoid) implement a much
    larger surface — but these three are the only ones L3 skill code
    should ever need.
    """

    capabilities: AdapterCapabilities

    def estop(self) -> None:
        """Non-BCI E-stop entry point. MUST be callable without holding
        any lock this adapter owns, and MUST return within 100 ms."""
        ...

    def get_base_pose(self) -> tuple[float, float, float]:
        """Return ``(x, y, theta)`` in world frame."""
        ...

    def set_base_velocity(self, v: float, w: float) -> None:
        """Commanded linear / angular velocity. Sticky until overwritten."""
        ...


class MockAdapter:
    """Null adapter for offline tests. Records commands; does nothing."""

    def __init__(self, name: str = "mock"):
        self.capabilities = AdapterCapabilities(
            name=name, mobile_base=True, manipulator=True, gripper=True
        )
        self._pose = (0.0, 0.0, 0.0)
        self.history: list[tuple[str, tuple]] = []
        self.estopped = False

    def estop(self) -> None:
        self.estopped = True
        self.history.append(("estop", ()))

    def get_base_pose(self) -> tuple[float, float, float]:
        return self._pose

    def set_base_velocity(self, v: float, w: float) -> None:
        self.history.append(("set_base_velocity", (v, w)))
