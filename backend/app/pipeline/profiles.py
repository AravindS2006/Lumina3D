from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


RuntimeProfileName = Literal["balanced", "quality", "low_vram"]


@dataclass(frozen=True)
class RuntimeProfile:
    name: RuntimeProfileName
    geometry_steps: int
    geometry_guidance_scale: float
    geometry_octree_resolution: int
    geometry_num_chunks: int
    texture_resolution: int
    texture_max_num_view: int
    texture_tiers: tuple[str, ...]


PROFILES: dict[str, RuntimeProfile] = {
    "balanced": RuntimeProfile(
        name="balanced",
        geometry_steps=24,
        geometry_guidance_scale=5.0,
        geometry_octree_resolution=256,
        geometry_num_chunks=16000,
        texture_resolution=512,
        texture_max_num_view=6,
        texture_tiers=("hunyuan21_pbr", "hunyuan20_paint"),
    ),
    "quality": RuntimeProfile(
        name="quality",
        geometry_steps=32,
        geometry_guidance_scale=5.0,
        geometry_octree_resolution=320,
        geometry_num_chunks=24000,
        texture_resolution=768,
        texture_max_num_view=8,
        texture_tiers=("hunyuan21_pbr", "hunyuan20_paint"),
    ),
    "low_vram": RuntimeProfile(
        name="low_vram",
        geometry_steps=16,
        geometry_guidance_scale=4.0,
        geometry_octree_resolution=196,
        geometry_num_chunks=8000,
        texture_resolution=512,
        texture_max_num_view=4,
        texture_tiers=("hunyuan20_paint", "hunyuan21_pbr"),
    ),
}


def resolve_profile(profile_name: str | None) -> RuntimeProfile:
    if not profile_name:
        return PROFILES["balanced"]
    return PROFILES.get(profile_name, PROFILES["balanced"])
