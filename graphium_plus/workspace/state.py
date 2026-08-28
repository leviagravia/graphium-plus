"""Small atomic recent-Workspace store; never session/root restoration authority."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from .model import normalize_root


RECENT_LIMIT = 8


class RecentWorkspaces:
    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)

    def paths(self) -> tuple[str, ...]:
        values = self._load()
        visible: list[str] = []
        for value in values:
            try:
                root = normalize_root(value)
            except Exception:
                continue
            if root not in visible:
                visible.append(root)
            if len(visible) >= RECENT_LIMIT:
                break
        return tuple(visible)

    def touch(self, root: str) -> tuple[str, ...]:
        canonical = normalize_root(root)
        current = list(self._load())
        values = [canonical, *(value for value in current if value != canonical)][:RECENT_LIMIT]
        self._save(tuple(values))
        return tuple(values)

    def _load(self) -> tuple[str, ...]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
            return ()
        if not isinstance(data, dict) or data.get("schema") != 1:
            return ()
        values = data.get("recent_roots")
        if not isinstance(values, list):
            return ()
        clean: list[str] = []
        for value in values:
            if isinstance(value, str) and value.strip():
                clean.append(os.path.abspath(os.path.expanduser(value.strip())))
            if len(clean) >= RECENT_LIMIT:
                break
        return tuple(clean)

    def _save(self, roots: tuple[str, ...]) -> None:
        parent = self.path.parent
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            os.chmod(parent, 0o700)
        except OSError:
            pass
        fd, temp_name = tempfile.mkstemp(prefix=".recent-workspaces-", suffix=".tmp", dir=parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump({"schema": 1, "recent_roots": list(roots)}, handle, ensure_ascii=False, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass
