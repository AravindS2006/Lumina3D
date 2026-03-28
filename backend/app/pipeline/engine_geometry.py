from __future__ import annotations

from pathlib import Path
from typing import Mapping

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

    def load(self) -> None:
        bootstrap = ensure_hunyuan_paths()
        if not bootstrap["paths_added"]:
            self.runtime_warnings.append(
                "Hunyuan runtime paths not found; geometry fallback may be used."
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
