from __future__ import annotations

import importlib
import importlib.util
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


def _safe_delete_module(module_name: str) -> bool:
    if module_name not in sys.modules:
        return False
    try:
        del sys.modules[module_name]
        return True
    except Exception:
        return False


def _module_belongs_to_root(module_obj: object, root_path: Path) -> bool:
    root_str = str(root_path)
    module_file = str(getattr(module_obj, "__file__", "") or "")
    if root_str and root_str in module_file:
        return True
    module_paths = [str(p) for p in getattr(module_obj, "__path__", [])]
    return any(root_str in p for p in module_paths)


def prepare_hy3dpaint_runtime() -> list[str]:
    """Resolve common import collisions for Hunyuan 2.1 paint stack.

    Hunyuan 2.1 `textureGenPipeline.py` imports from bare module names like
    `utils.*` and `DifferentiableRenderer.*`. In many environments another
    top-level module named `utils` is already loaded, causing:
    "No module named 'utils.simplify_mesh_utils'; 'utils' is not a package".
    """

    warnings: list[str] = []
    bootstrap = ensure_hunyuan_paths()
    del bootstrap

    root_candidates = [
        os.getenv("LUMINA_HUNYUAN21_ROOT"),
        "/content/Hunyuan3D-2.1",
        "/content/Lumina3D/backend/vendor/Hunyuan3D-2.1",
    ]

    hy3dpaint_root: Path | None = None
    for root_value in root_candidates:
        if not root_value:
            continue
        candidate = Path(root_value) / "hy3dpaint"
        if candidate.exists():
            hy3dpaint_root = candidate
            _append_if_exists(candidate)
            break

    if hy3dpaint_root is None:
        warnings.append("hy3dpaint root not found; cannot prepare paint runtime")
        return warnings

    for module_name in ("utils", "DifferentiableRenderer"):
        loaded = sys.modules.get(module_name)
        if loaded is None:
            continue

        owned_by_hy3dpaint = _module_belongs_to_root(loaded, hy3dpaint_root)

        if not owned_by_hy3dpaint and _safe_delete_module(module_name):
            warnings.append(
                f"Removed conflicting module '{module_name}' before importing hy3dpaint"
            )

    # Expose hy3dpaint-local aliases for pipelines using bare imports.
    _safe_delete_module("utils")
    _safe_delete_module("DifferentiableRenderer")

    for alias_name, rel_path in (
        ("utils", "utils"),
        ("DifferentiableRenderer", "DifferentiableRenderer"),
    ):
        if alias_name in sys.modules and _module_belongs_to_root(
            sys.modules[alias_name], hy3dpaint_root
        ):
            continue
        target_path = hy3dpaint_root / rel_path
        if not target_path.exists():
            continue
        try:
            spec = importlib.util.spec_from_file_location(
                alias_name,
                target_path / "__init__.py",
                submodule_search_locations=[str(target_path)],
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                sys.modules[alias_name] = module
                warnings.append(f"Injected hy3dpaint alias module '{alias_name}'")
        except Exception as exc:
            warnings.append(f"Failed to inject alias '{alias_name}': {exc}")

    return warnings


def probe_hunyuan_runtime() -> dict[str, object]:
    bootstrap = ensure_hunyuan_paths()
    module_checks: dict[str, str] = {}
    warnings: list[str] = []

    warnings.extend(prepare_hy3dpaint_runtime())

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
        "warnings": warnings,
    }


def get_hf_cache_info() -> dict[str, object]:
    cache_root = Path(
        os.path.expanduser(os.getenv("HY3DGEN_MODELS", "~/.cache/hy3dgen"))
    )
    hy2mv_dir = cache_root / "tencent" / "Hunyuan3D-2mv"

    def _dir_size_mb(path: Path) -> float:
        if not path.exists():
            return 0.0
        total = 0
        for p in path.rglob("*"):
            if p.is_file():
                total += p.stat().st_size
        return round(total / (1024 * 1024), 2)

    return {
        "cache_root": str(cache_root),
        "hunyuan2mv_present": hy2mv_dir.exists(),
        "hunyuan2mv_size_mb": _dir_size_mb(hy2mv_dir),
    }
