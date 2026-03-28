from __future__ import annotations

from pathlib import Path

from PIL import Image
import trimesh


class TextureEngine:
    """Stage 2 texture generation wrapper for Hunyuan3D-2.1 paint module."""

    def __init__(self, model_id: str = "tencent/Hunyuan3D-2.1") -> None:
        self.model_id = model_id
        self._pipeline = None

    def load(self) -> None:
        # TODO: replace with real Hunyuan3D-2.1 paint pipeline initialization.
        self._pipeline = self.model_id

    def apply_pbr(
        self, input_mesh_path: Path, output_glb_path: Path, texture_dir: Path
    ) -> Path:
        texture_dir.mkdir(parents=True, exist_ok=True)
        self._create_placeholder_textures(texture_dir)

        scene = trimesh.load(input_mesh_path, force="mesh")
        scene.export(output_glb_path)
        return output_glb_path

    def _create_placeholder_textures(self, texture_dir: Path) -> None:
        size = (1024, 1024)
        Image.new("RGB", size, color=(190, 190, 200)).save(texture_dir / "albedo.png")
        Image.new("L", size, color=120).save(texture_dir / "roughness.png")
        Image.new("L", size, color=20).save(texture_dir / "metallic.png")
        Image.new("RGB", size, color=(128, 128, 255)).save(texture_dir / "normal.png")

    def unload(self) -> None:
        self._pipeline = None
