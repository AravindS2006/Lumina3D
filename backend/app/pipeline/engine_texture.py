from __future__ import annotations

from pathlib import Path

import trimesh

from app.pipeline.profiles import RuntimeProfile
from app.pipeline.runtime_bootstrap import ensure_hunyuan_paths


class TextureEngine:
    """Stage 2 texturing with tiered runtime selection.

    Tier 1: Hunyuan3D-2.1 PBR paint stack
    Tier 2: Hunyuan3D-2.0 paint stack fallback
    """

    def __init__(self) -> None:
        self._pipeline = None
        self.active_tier: str | None = None
        self.runtime_warnings: list[str] = []

    def load(self, tier: str, profile: RuntimeProfile) -> None:
        del profile
        ensure_hunyuan_paths()

        if tier == "hunyuan21_pbr":
            self._load_hunyuan21()
            self.active_tier = tier
            return

        if tier == "hunyuan20_paint":
            self._load_hunyuan20()
            self.active_tier = tier
            return

        raise ValueError(f"Unknown texture tier: {tier}")

    def _load_hunyuan21(self) -> None:
        from hy3dpaint.textureGenPipeline import (  # type: ignore
            Hunyuan3DPaintConfig,
            Hunyuan3DPaintPipeline,
        )

        config = Hunyuan3DPaintConfig(max_num_view=6, resolution=512)
        self._pipeline = Hunyuan3DPaintPipeline(config)

    def _load_hunyuan20(self) -> None:
        from hy3dgen.texgen import Hunyuan3DPaintPipeline  # type: ignore

        self._pipeline = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")

    def apply_pbr(
        self,
        input_mesh_path: Path,
        output_glb_path: Path,
        reference_image_path: Path,
        profile: RuntimeProfile,
    ) -> Path:
        if self._pipeline is None or self.active_tier is None:
            raise RuntimeError("Texture pipeline is not loaded")

        if self.active_tier == "hunyuan21_pbr":
            return self._apply_hunyuan21(
                input_mesh_path=input_mesh_path,
                output_glb_path=output_glb_path,
                reference_image_path=reference_image_path,
                profile=profile,
            )

        if self.active_tier == "hunyuan20_paint":
            return self._apply_hunyuan20(
                input_mesh_path=input_mesh_path,
                output_glb_path=output_glb_path,
                reference_image_path=reference_image_path,
            )

        raise RuntimeError(f"Unsupported active texture tier: {self.active_tier}")

    def _apply_hunyuan21(
        self,
        input_mesh_path: Path,
        output_glb_path: Path,
        reference_image_path: Path,
        profile: RuntimeProfile,
    ) -> Path:
        del profile
        textured_obj_path = output_glb_path.with_suffix(".obj")
        result_path = self._pipeline(
            mesh_path=str(input_mesh_path),
            image_path=str(reference_image_path),
            output_mesh_path=str(textured_obj_path),
            save_glb=False,
        )

        textured_mesh = trimesh.load(result_path, force="mesh")
        textured_mesh.export(output_glb_path)
        return output_glb_path

    def _apply_hunyuan20(
        self,
        input_mesh_path: Path,
        output_glb_path: Path,
        reference_image_path: Path,
    ) -> Path:
        mesh = trimesh.load(input_mesh_path, force="mesh")
        textured_mesh = self._pipeline(mesh, image=str(reference_image_path))
        textured_mesh.export(output_glb_path)
        return output_glb_path

    def unload(self) -> None:
        self._pipeline = None
        self.active_tier = None
