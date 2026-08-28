"""Stable Graphium product identity."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProductIdentity:
    product_name: str
    package_name: str
    executable_name: str
    version: str | None
    desktop_application_id: str
    application_icon_name: str
    xdg_namespace: str
    author: str
    copyright: str
    license_id: str
    repository_url: str
    repository_label: str


CORE_PRODUCT_IDENTITY = ProductIdentity(
    product_name="Graphium",
    package_name="graphium",
    executable_name="graphium",
    version="0.0.16",
    desktop_application_id="io.github.leviagravia.Graphium",
    application_icon_name="io.github.leviagravia.Graphium",
    xdg_namespace="graphium",
    author="leviagravia@zohomail.eu",
    copyright="Copyright © 2026 leviagravia",
    license_id="GPL-3.0-or-later",
    repository_url="https://github.com/leviagravia/graphium",
    repository_label="Graphium repository",
)

PRODUCT_NAME = CORE_PRODUCT_IDENTITY.product_name
PACKAGE_NAME = CORE_PRODUCT_IDENTITY.package_name
EXECUTABLE_NAME = CORE_PRODUCT_IDENTITY.executable_name
VERSION = CORE_PRODUCT_IDENTITY.version
DESKTOP_APPLICATION_ID = CORE_PRODUCT_IDENTITY.desktop_application_id
APPLICATION_ICON_NAME = CORE_PRODUCT_IDENTITY.application_icon_name
AUTHOR = CORE_PRODUCT_IDENTITY.author
COPYRIGHT = CORE_PRODUCT_IDENTITY.copyright
LICENSE_ID = CORE_PRODUCT_IDENTITY.license_id
REPOSITORY_URL = CORE_PRODUCT_IDENTITY.repository_url
REPOSITORY_LABEL = CORE_PRODUCT_IDENTITY.repository_label
