"""Pure XDG path resolution for Graphium.

This module resolves paths only. It performs no filesystem mutation.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class XdgPaths:
    config: Path
    data: Path
    cache: Path
    state: Path


def _home(env: Mapping[str, str]) -> Path:
    raw = env.get("HOME")
    if not raw:
        raise ValueError("HOME is required to resolve Graphium XDG paths")
    return Path(raw)


def resolve_xdg_paths(
    env: Mapping[str, str] | None = None, *, namespace: str = "graphium"
) -> XdgPaths:
    source = os.environ if env is None else env
    home = _home(source)
    config_home = Path(source.get("XDG_CONFIG_HOME", home / ".config"))
    data_home = Path(source.get("XDG_DATA_HOME", home / ".local" / "share"))
    cache_home = Path(source.get("XDG_CACHE_HOME", home / ".cache"))
    state_home = Path(source.get("XDG_STATE_HOME", home / ".local" / "state"))
    return XdgPaths(
        config=config_home / namespace,
        data=data_home / namespace,
        cache=cache_home / namespace,
        state=state_home / namespace,
    )

def resolve_recovery_root(env: Mapping[str, str] | None = None) -> Path:
    """Return the private Graphium crash-recovery root without creating it."""
    return resolve_xdg_paths(env).state / "recovery"

