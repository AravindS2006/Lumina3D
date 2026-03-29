from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

import torch
import trimesh

from app.pipeline.profiles import RuntimeProfile
from app.pipeline.runtime_bootstrap import ensure_hunyuan_paths


class GeometryEngine:
    """Stage 1 geometry generation via Hunyuan3D-2mv.

    Falls back to a deterministic primitive only when runtime bootstrap
    cannot import the required model package.
    """

    def __init__(self, model_id: str = "tencent/Hunyuan3D-2mv") -> None:
        self.model_id = model_id
        self._pipeline = None
        self.runtime_warnings: list[str] = []

    def _hy3d_cache_dir(self) -> Path:
        base = os.path.expanduser(os.getenv("HY3DGEN_MODELS", "~/.cache/hy3dgen"))
        return Path(base) / "tencent" / "Hunyuan3D-2mv" / "hunyuan3d-dit-v2-mv"

    def is_cached(self) -> bool:
        return self._hy3d_cache_dir().exists()

    def load(self) -> None:
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA is unavailable. Hunyuan3D-2mv geometry generation requires a GPU runtime (for example, Colab T4)."
            )

        bootstrap = ensure_hunyuan_paths()
        if not bootstrap["paths_added"]:
            self.runtime_warnings.append(
                "Hunyuan runtime paths not found; geometry fallback may be used."
            )

        cache_dir = self._hy3d_cache_dir()
        if not cache_dir.exists():
            self.runtime_warnings.append(
                f"Model cache not found at {cache_dir}. First run will download weights."
            )
        else:
            self.runtime_warnings.append(
                f"Using cached geometry weights from {cache_dir}"
            )

        from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline  # type: ignore

        self._pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            self.model_id,
            subfolder="hunyuan3d-dit-v2-mv",
            use_safetensors=False,
            device="cuda",
        )

    def generate_mesh(
        self,
        image_views: Mapping[str, Path],
        output_mesh_path: Path,
        profile: RuntimeProfile,
    ) -> Path:
        if not image_views:
            raise ValueError(
                "At least one view image is required for geometry generation"
            )

        if self._pipeline is None:
            raise RuntimeError("Geometry pipeline is not loaded")

        view_payload: dict[str, str] = {
            key: str(path)
            for key, path in image_views.items()
            if key in {"front", "left", "back", "right"}
        }
        if not view_payload:
            raise ValueError(
                "No valid view labels found. Expected front/left/back/right"
            )

        outputs = self._pipeline(
            image=view_payload,
            num_inference_steps=profile.geometry_steps,
            guidance_scale=profile.geometry_guidance_scale,
            octree_resolution=profile.geometry_octree_resolution,
            num_chunks=profile.geometry_num_chunks,
            output_type="trimesh",
        )
        if not outputs:
            raise RuntimeError("Geometry pipeline returned no mesh output")

        mesh = outputs[0]
        if not isinstance(mesh, trimesh.Trimesh):
            raise RuntimeError("Unexpected geometry output type from Hunyuan pipeline")

        mesh.export(output_mesh_path)
        return output_mesh_path

    def unload(self) -> None:
        self._pipeline = None
