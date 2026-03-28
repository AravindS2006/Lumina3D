from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


def _append_if_exists(path: Path) -> bool:
    if not path.exists():
        return False
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)
    return True


def ensure_hunyuan_paths() -> dict[str, list[str]]:
    """Expose common Hunyuan repository roots to Python import path.

    Returns a dict describing which roots were injected.
    """

    added: list[str] = []

    candidate_roots = [
        os.getenv("LUMINA_HUNYUAN21_ROOT"),
        os.getenv("LUMINA_HUNYUAN2_ROOT"),
        "/content/Hunyuan3D-2.1",
        "/content/Hunyuan3D-2",
        "/content/Lumina3D/backend/vendor/Hunyuan3D-2.1",
        "/content/Lumina3D/backend/vendor/Hunyuan3D-2",
    ]

    for root_value in candidate_roots:
        if not root_value:
            continue
        root = Path(root_value)
        if _append_if_exists(root):
            added.append(str(root))

        # Hunyuan 2.1 local package layout
        for nested in (
            "hy3dshape",
            "hy3dpaint",
            "hy3dpaint/hy3dpaint",
            "hy3dshape/hy3dshape",
        ):
            nested_path = root / nested
            if _append_if_exists(nested_path):
                added.append(str(nested_path))

        # Hunyuan 2.0 style package layout
        for nested in ("hy3dgen", "hy3dgen/texgen", "hy3dgen/shapegen"):
            nested_path = root / nested
            if _append_if_exists(nested_path):
                added.append(str(nested_path))

    return {"paths_added": sorted(set(added))}


def probe_hunyuan_runtime() -> dict[str, object]:
    bootstrap = ensure_hunyuan_paths()
    module_checks: dict[str, str] = {}

    modules = (
        "hy3dgen.shapegen",
        "hy3dgen.texgen",
        "hy3dpaint.textureGenPipeline",
    )

    for module_name in modules:
        try:
            importlib.import_module(module_name)
            module_checks[module_name] = "ok"
        except Exception as exc:
            module_checks[module_name] = f"error: {exc}"

    return {
        "paths_added": bootstrap["paths_added"],
        "module_checks": module_checks,
    }
