"""Graphium Plus product identity."""
from __future__ import annotations

from dataclasses import replace

from graphium.product import CORE_PRODUCT_IDENTITY


PLUS_PRODUCT_IDENTITY = replace(
    CORE_PRODUCT_IDENTITY,
    product_name="Graphium Plus",
    package_name="graphium-plus",
    executable_name="graphium-plus",
    version="0.0.2",
    desktop_application_id="io.github.leviagravia.GraphiumPlus",
    application_icon_name="io.github.leviagravia.GraphiumPlus",
    xdg_namespace="graphium-plus",
    repository_url="https://github.com/leviagravia/graphium-plus",
    repository_label="Graphium Plus repository",
)
