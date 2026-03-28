from __future__ import annotations

from pathlib import Path
from typing import Sequence

import trimesh


class GeometryEngine:
    """Stage 1 geometry generation wrapper for Hunyuan3D-2mv.

    This class keeps integration points explicit while still producing
    a valid mesh in environments where the model is unavailable.
    """

    def __init__(self, model_id: str = "tencent/Hunyuan3D-2mv") -> None:
        self.model_id = model_id
        self._pipeline = None

    def load(self) -> None:
        # TODO: replace with real Hunyuan3D-2mv pipeline initialization.
        # Keep lazy-loading so VRAM is only used during this stage.
        self._pipeline = self.model_id

    def generate_mesh(
        self, image_paths: Sequence[Path], output_mesh_path: Path
    ) -> Path:
        if not image_paths:
            raise ValueError("At least one image is required for geometry generation")

        # Placeholder mesh generation for bootstrap/testing.
        # Swap with actual inference call from Hunyuan3D-2mv when runtime is prepared.
        mesh = trimesh.creation.icosphere(subdivisions=3, radius=0.6)
        mesh.export(output_mesh_path)
        return output_mesh_path

    def unload(self) -> None:
        self._pipeline = None
