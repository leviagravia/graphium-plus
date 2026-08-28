"""GTK3 application root for Graphium Plus."""
from __future__ import annotations

from pathlib import Path

from graphium.adapters.gtk.application import GraphiumApplication
from graphium_plus.product import PLUS_PRODUCT_IDENTITY
from .window import GraphiumPlusWindow


_ICON_ROOT = Path(__file__).resolve().parents[2] / "data" / "icons" / "hicolor"


class GraphiumPlusApplication(GraphiumApplication):
    def __init__(self) -> None:
        super().__init__(
            identity=PLUS_PRODUCT_IDENTITY,
            window_factory=GraphiumPlusWindow,
            icon_root=_ICON_ROOT,
        )
