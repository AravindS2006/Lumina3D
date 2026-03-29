from __future__ import annotations

import json
import logging
import os
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
from threading import Lock
from time import perf_counter
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import torch

from app.pipeline.engine_geometry import GeometryEngine
from app.pipeline.engine_texture import TextureEngine
from app.pipeline.profiles import RuntimeProfile, resolve_profile
from app.pipeline.runtime_bootstrap import get_hf_cache_info, probe_hunyuan_runtime
from app.pipeline.vram import purge_cuda_memory
from app.schemas.job import JobStatusResponse
from app.utils.error_codes import map_failure_code
from app.utils.file_io import TMP_DIR, UPLOADS_DIR, ensure_dirs, job_dir
from app.utils.frame_extractor import extract_keyframes
from app.utils.job_store import JobStore


logger = logging.getLogger("lumina3d.api")
MODEL_DOWNLOAD_LOCK = Lock()
_pipeline_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pipeline")

app = FastAPI(title="Lumina3D API", version="0.2.0")
job_store = JobStore()
pipeline_lock = Lock()

VALID_VIEWS = ("front", "left", "back", "right")
FALLBACK_VIEW_ORDER = ("front", "left", "back", "right")


app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    ensure_dirs()
    logger.info("Lumina3D API startup complete")


@app.get("/")
def root() -> dict[str, object]:
    return {
        "name": "Lumina3D API",
        "status": "ok",
        "profiles": ["balanced", "low_vram", "quality"],
        "docs": "/docs",
        "health": "/healthz",
        "endpoints": {
            "generate": "POST /generate",
            "status": "GET /status/{job_id}",
            "download": "GET /download/{job_id}",
        },
    }


@app.get("/healthz")
def healthz() -> dict[str, object]:
    return {
        "status": "ok",
        "api_version": app.version,
        "runtime_probe": True,
        "cuda_available": torch.cuda.is_available(),
    }


@app.get("/debug/runtime")
def debug_runtime() -> dict[str, object]:
    """Quick runtime diagnostics for model imports and path bootstrapping."""
    payload = probe_hunyuan_runtime()
    payload["cache_info"] = get_hf_cache_info()
    return payload


@app.post("/generate")
async def generate(
    video: Optional[UploadFile] = File(default=None),
    images: Optional[list[UploadFile]] = File(default=None),
    profile: str = Form(default="balanced"),
    view_labels: Optional[str] = Form(default=None),
) -> dict[str, str]:
    require_cuda = os.getenv("LUMINA_REQUIRE_CUDA", "1") == "1"
    if require_cuda and not torch.cuda.is_available():
        raise HTTPException(
            status_code=503,
            detail="CUDA GPU is required for generation. Use Colab GPU runtime or set LUMINA_REQUIRE_CUDA=0 explicitly for local debug.",
        )

    if video is None and not images:
        raise HTTPException(status_code=400, detail="Provide either a video or images")
    if video is not None and images:
        raise HTTPException(status_code=400, detail="Provide video or images, not both")

    runtime_profile = resolve_profile(profile)
    parsed_labels = _parse_view_labels(view_labels)

    job_id = str(uuid.uuid4())
    job_store.create(job_id, profile=runtime_profile.name)

    upload_dir = UPLOADS_DIR / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    video_path: Optional[Path] = None
    image_paths: list[Path] = []
    image_names: list[str] = []

    if video is not None:
        if not (video.filename or "").lower().endswith(".mp4"):
            raise HTTPException(status_code=400, detail="Video must be .mp4")

        video_path = upload_dir / "input.mp4"
        with video_path.open("wb") as handle:
            shutil.copyfileobj(video.file, handle)
    else:
        for idx, file in enumerate(images or []):
            original_name = file.filename or f"image_{idx}.png"
            suffix = Path(original_name).suffix or ".png"
            img_path = upload_dir / f"input_{idx}{suffix}"
            with img_path.open("wb") as handle:
                shutil.copyfileobj(file.file, handle)
            image_paths.append(img_path)
            image_names.append(original_name)

    _pipeline_executor.submit(
        run_job_pipeline,
        job_id,
        video_path,
        image_paths,
        image_names,
        runtime_profile,
        parsed_labels,
    )
    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}", response_model=JobStatusResponse)
def status(job_id: str) -> JobStatusResponse:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        stage=job.stage,
        message=job.message,
        download_url=f"/download/{job_id}" if job.output_glb_path else None,
        profile=job.profile,
        engine_tier=job.engine_tier,
        failure_code=job.failure_code,
        warnings=job.warnings,
        stage_timings=job.stage_timings,
        created_at=job.created_at,
        updated_at=job.updated_at,
        error=job.error,
    )


@app.get("/download/{job_id}")
def download(job_id: str) -> FileResponse:
    job = job_store.get(job_id)
    if not job or not job.output_glb_path:
        raise HTTPException(status_code=404, detail="Output not available")

    return FileResponse(
        path=job.output_glb_path,
        filename=f"{job_id}.glb",
        media_type="model/gltf-binary",
    )


def _parse_view_labels(raw_view_labels: Optional[str]) -> dict[str, str]:
    if not raw_view_labels:
        return {}

    try:
        payload = json.loads(raw_view_labels)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400, detail=f"view_labels must be valid JSON: {exc}"
        )

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="view_labels must be a JSON object")

    parsed: dict[str, str] = {}
    for raw_key, raw_label in payload.items():
        if not isinstance(raw_label, str):
            continue
        label = raw_label.strip().lower()
        if label in VALID_VIEWS:
            parsed[str(raw_key)] = label
    return parsed


def _infer_view_from_name(name: str) -> Optional[str]:
    lowered = name.lower()
    if "front" in lowered:
        return "front"
    if "left" in lowered:
        return "left"
    if "back" in lowered:
        return "back"
    if "right" in lowered:
        return "right"
    return None


def _resolve_view_images(
    image_paths: list[Path], image_names: list[str], view_labels: dict[str, str]
) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    pending: list[Path] = []

    for index, path in enumerate(image_paths):
        name = image_names[index] if index < len(image_names) else path.name
        explicit_label = None

        for key in (str(index), name, path.name, path.stem):
            if key in view_labels:
                explicit_label = view_labels[key]
                break

        inferred_label = explicit_label or _infer_view_from_name(name)
        if inferred_label and inferred_label not in resolved:
            resolved[inferred_label] = path
            continue
        pending.append(path)

    for path in pending:
        free_slot = next(
            (label for label in FALLBACK_VIEW_ORDER if label not in resolved), None
        )
        if free_slot is None:
            break
        resolved[free_slot] = path

    return resolved


def _mark_stage(
    job_id: str,
    *,
    status: Optional[str],
    progress: int,
    stage: str,
    message: str,
    warnings: list[str],
    stage_timings: dict[str, float],
    engine_tier: Optional[str] = None,
) -> None:
    job_store.update(
        job_id,
        status=status,
        progress=progress,
        stage=stage,
        message=message,
        warnings=warnings,
        stage_timings=stage_timings,
        engine_tier=engine_tier,
    )


def run_job_pipeline(
    job_id: str,
    video_path: Optional[Path],
    image_paths: list[Path],
    image_names: list[str],
    profile: RuntimeProfile,
    view_labels: dict[str, str],
) -> None:
    timings: dict[str, float] = {}
    warnings: list[str] = []
    used_texture_tier: Optional[str] = None
    lock_acquired = False

    lock_start = perf_counter()
    lock_acquired = pipeline_lock.acquire(blocking=False)
    if not lock_acquired:
        _mark_stage(
            job_id,
            status="queued",
            progress=1,
            stage="waiting_gpu",
            message="Waiting for GPU slot",
            warnings=warnings,
            stage_timings=timings,
        )
        pipeline_lock.acquire()
        lock_acquired = True
    timings["wait_for_gpu"] = round(perf_counter() - lock_start, 3)

    try:
        _mark_stage(
            job_id,
            status="running",
            progress=5,
            stage="preparing",
            message="Preparing inputs",
            warnings=warnings,
            stage_timings=timings,
        )

        stage_start = perf_counter()
        working_dir = job_dir(job_id)
        frames_dir = TMP_DIR / job_id / "frames"
        mesh_path = working_dir / "geometry.obj"
        glb_path = working_dir / "result.glb"
        timings["prepare_directories"] = round(perf_counter() - stage_start, 3)

        if video_path is not None:
            _mark_stage(
                job_id,
                status=None,
                progress=18,
                stage="extracting_frames",
                message="Extracting Front/Right/Back/Left frames",
                warnings=warnings,
                stage_timings=timings,
            )
            stage_start = perf_counter()
            extracted = extract_keyframes(video_path, frames_dir)
            image_views = extracted
            timings["extract_frames"] = round(perf_counter() - stage_start, 3)
        else:
            stage_start = perf_counter()
            image_views = _resolve_view_images(image_paths, image_names, view_labels)
            timings["resolve_view_labels"] = round(perf_counter() - stage_start, 3)

        if not image_views:
            raise ValueError("No usable image views found after preprocessing")

        stage_start = perf_counter()
        geometry_engine = GeometryEngine()
        needs_download = not geometry_engine.is_cached()

        load_timeout_s = int(os.getenv("LUMINA_GEOMETRY_LOAD_TIMEOUT", "900"))

        if needs_download:
            _mark_stage(
                job_id,
                status=None,
                progress=31,
                stage="download_weights",
                message=(
                    f"Hunyuan3D-2mv weights not cached. Downloading from Hugging Face "
                    f"(up to {load_timeout_s // 60} min on first run)..."
                ),
                warnings=warnings,
                stage_timings=timings,
            )
        else:
            _mark_stage(
                job_id,
                status=None,
                progress=32,
                stage="loading_geometry",
                message="Loading cached Hunyuan3D-2mv weights into GPU...",
                warnings=warnings,
                stage_timings=timings,
            )

        load_done = threading.Event()

        def _mem_snapshot() -> str:
            parts: list[str] = []
            try:
                import psutil  # type: ignore[import-untyped]

                vm = psutil.virtual_memory()
                parts.append(f"RAM {vm.percent:.0f}%")
            except Exception:
                pass
            if torch.cuda.is_available():
                try:
                    alloc = torch.cuda.memory_allocated() / (1024**3)
                    reserved = torch.cuda.memory_reserved() / (1024**3)
                    parts.append(f"VRAM {alloc:.1f}/{reserved:.1f}GB")
                except Exception:
                    pass
            return f" [{' ,'.join(parts)}]" if parts else ""

        def _load_heartbeat() -> None:
            while not load_done.is_set():
                load_done.wait(timeout=10)
                if load_done.is_set():
                    break
                elapsed_s = round(perf_counter() - stage_start, 0)
                mem = _mem_snapshot()
                if needs_download:
                    _mark_stage(
                        job_id,
                        status=None,
                        progress=33,
                        stage="download_weights",
                        message=(
                            f"Still downloading Hunyuan3D-2mv weights... "
                            f"({int(elapsed_s)}s elapsed){mem}. "
                            f"This is normal for first run on a new Colab session."
                        ),
                        warnings=warnings,
                        stage_timings=timings,
                    )
                else:
                    _mark_stage(
                        job_id,
                        status=None,
                        progress=34,
                        stage="loading_geometry",
                        message=(
                            f"Loading model into GPU memory... "
                            f"({int(elapsed_s)}s elapsed){mem}"
                        ),
                        warnings=warnings,
                        stage_timings=timings,
                    )

        heartbeat = threading.Thread(target=_load_heartbeat, daemon=True)

        load_error: list[Exception] = []

        def _run_load() -> None:
            try:
                geometry_engine.load()
            except Exception as exc:  # noqa: BLE001
                load_error.append(exc)
            finally:
                load_done.set()

        load_thread = threading.Thread(target=_run_load, daemon=True)

        with MODEL_DOWNLOAD_LOCK:
            heartbeat.start()
            load_thread.start()
            load_thread.join(timeout=load_timeout_s)

        load_done.set()
        heartbeat.join(timeout=15)

        if not load_thread.is_alive() and load_error:
            raise load_error[0]

        if load_thread.is_alive():
            raise RuntimeError(
                f"Geometry engine load timed out after {load_timeout_s}s. "
                "Possible causes: very slow download, GPU unavailable, or hung model init. "
                "Set LUMINA_GEOMETRY_LOAD_TIMEOUT env var to increase the limit."
            )

        warnings.extend(geometry_engine.runtime_warnings)
        load_elapsed = round(perf_counter() - stage_start, 3)
        timings["load_geometry_engine"] = load_elapsed
        logger.info(
            "Geometry engine loaded in %.1fs (download_needed=%s)",
            load_elapsed,
            needs_download,
        )

        _mark_stage(
            job_id,
            status=None,
            progress=45,
            stage="generating_geometry",
            message="Generating mesh geometry",
            warnings=warnings,
            stage_timings=timings,
        )
        stage_start = perf_counter()
        geometry_engine.generate_mesh(image_views, mesh_path, profile)
        timings["generate_geometry"] = round(perf_counter() - stage_start, 3)

        _mark_stage(
            job_id,
            status=None,
            progress=58,
            stage="cleanup_geometry",
            message="Cleaning geometry model from VRAM",
            warnings=warnings,
            stage_timings=timings,
        )
        stage_start = perf_counter()
        geometry_engine.unload()
        del geometry_engine
        purge_cuda_memory()
        timings["cleanup_geometry"] = round(perf_counter() - stage_start, 3)

        reference_image_path = image_views.get("front") or next(
            iter(image_views.values())
        )
        texture_exception: Optional[Exception] = None

        for tier in profile.texture_tiers:
            _mark_stage(
                job_id,
                status=None,
                progress=66,
                stage="loading_texture",
                message=f"Loading texture tier: {tier}",
                warnings=warnings,
                stage_timings=timings,
                engine_tier=tier,
            )

            texture_engine = TextureEngine()
            tier_key = tier.replace("-", "_")

            try:
                stage_start = perf_counter()
                texture_engine.load(tier=tier, profile=profile)
                warnings.extend(texture_engine.runtime_warnings)
                timings[f"load_texture_{tier_key}"] = round(
                    perf_counter() - stage_start, 3
                )

                _mark_stage(
                    job_id,
                    status=None,
                    progress=80,
                    stage="applying_pbr",
                    message=f"Applying PBR textures with {tier}",
                    warnings=warnings,
                    stage_timings=timings,
                    engine_tier=tier,
                )

                stage_start = perf_counter()
                texture_engine.apply_pbr(
                    input_mesh_path=mesh_path,
                    output_glb_path=glb_path,
                    reference_image_path=reference_image_path,
                    profile=profile,
                )
                timings[f"apply_pbr_{tier_key}"] = round(
                    perf_counter() - stage_start, 3
                )
                used_texture_tier = tier
                break
            except Exception as exc:
                texture_exception = exc
                warnings.append(f"Texture tier {tier} failed: {exc}")
            finally:
                stage_start = perf_counter()
                texture_engine.unload()
                del texture_engine
                purge_cuda_memory()
                timings[f"cleanup_texture_{tier_key}"] = round(
                    perf_counter() - stage_start,
                    3,
                )

        if used_texture_tier is None:
            if texture_exception is None:
                raise RuntimeError("No texture tiers executed")
            raise texture_exception

        if not glb_path.exists():
            raise RuntimeError("Expected output GLB file was not created")

        _mark_stage(
            job_id,
            status="complete",
            progress=100,
            stage="complete",
            message="3D model is ready",
            warnings=warnings,
            stage_timings=timings,
            engine_tier=used_texture_tier,
        )
        job_store.update(
            job_id, output_glb_path=str(glb_path), engine_tier=used_texture_tier
        )
    except Exception as exc:
        purge_cuda_memory()
        failure_code = map_failure_code(exc)
        failure_stage = "failed"
        failure_message = "Generation failed"

        if failure_code == "cuda_unavailable":
            failure_stage = "geometry_runtime_unavailable"
            failure_message = "CUDA GPU runtime unavailable. Switch to Colab GPU runtime and restart backend."

        job_store.update(
            job_id,
            status="failed",
            stage=failure_stage,
            progress=100,
            message=failure_message,
            failure_code=failure_code,
            warnings=warnings,
            stage_timings=timings,
            error=str(exc),
        )
    finally:
        if lock_acquired:
            pipeline_lock.release()
