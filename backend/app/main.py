from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pyngrok import ngrok

from app.pipeline.engine_geometry import GeometryEngine
from app.pipeline.engine_texture import TextureEngine
from app.pipeline.vram import purge_cuda_memory
from app.schemas.job import JobStatusResponse
from app.utils.file_io import TMP_DIR, UPLOADS_DIR, ensure_dirs, job_dir
from app.utils.frame_extractor import extract_keyframes
from app.utils.job_store import JobStore


app = FastAPI(title="Lumina3D API", version="0.1.0")
job_store = JobStore()
ngrok_url: Optional[str] = None


app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    global ngrok_url
    ensure_dirs()
    token = os.getenv("NGROK_AUTHTOKEN")
    enable_ngrok = os.getenv("ENABLE_NGROK", "0") == "1"
    if token and enable_ngrok:
        ngrok.set_auth_token(token)
        tunnel = ngrok.connect(addr=8000)
        ngrok_url = tunnel.public_url


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "ngrok_url": ngrok_url or "disabled"}


@app.post("/generate")
async def generate(
    background_tasks: BackgroundTasks,
    video: Optional[UploadFile] = File(default=None),
    images: Optional[list[UploadFile]] = File(default=None),
) -> dict[str, str]:
    if video is None and not images:
        raise HTTPException(status_code=400, detail="Provide either a video or images")
    if video is not None and images:
        raise HTTPException(status_code=400, detail="Provide video or images, not both")

    job_id = str(uuid.uuid4())
    job_store.create(job_id)

    upload_dir = UPLOADS_DIR / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    video_path: Optional[Path] = None
    image_paths: list[Path] = []

    if video is not None:
        if not video.filename.lower().endswith(".mp4"):
            raise HTTPException(status_code=400, detail="Video must be .mp4")
        video_path = upload_dir / "input.mp4"
        with video_path.open("wb") as handle:
            shutil.copyfileobj(video.file, handle)
    else:
        for idx, file in enumerate(images or []):
            suffix = Path(file.filename or f"img_{idx}.png").suffix or ".png"
            img_path = upload_dir / f"input_{idx}{suffix}"
            with img_path.open("wb") as handle:
                shutil.copyfileobj(file.file, handle)
            image_paths.append(img_path)

    background_tasks.add_task(run_job_pipeline, job_id, video_path, image_paths)
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


def run_job_pipeline(
    job_id: str, video_path: Optional[Path], image_paths: list[Path]
) -> None:
    try:
        job_store.update(
            job_id,
            status="running",
            progress=5,
            stage="preparing",
            message="Preparing inputs",
        )

        working_dir = job_dir(job_id)
        frames_dir = TMP_DIR / job_id / "frames"
        mesh_path = working_dir / "geometry.obj"
        glb_path = working_dir / "result.glb"
        texture_dir = working_dir / "textures"

        if video_path is not None:
            job_store.update(
                job_id,
                progress=20,
                stage="extracting_frames",
                message="Extracting Front/Right/Back/Left frames",
            )
            image_paths = extract_keyframes(video_path, frames_dir)

        job_store.update(
            job_id,
            progress=35,
            stage="generating_geometry",
            message="Loading Hunyuan3D-2mv",
        )
        geometry_engine = GeometryEngine()
        geometry_engine.load()
        job_store.update(
            job_id,
            progress=50,
            stage="generating_geometry",
            message="Generating geometry mesh",
        )
        geometry_engine.generate_mesh(image_paths, mesh_path)
        geometry_engine.unload()
        del geometry_engine
        purge_cuda_memory()

        job_store.update(
            job_id, progress=65, stage="applying_pbr", message="Loading Hunyuan3D-2.1"
        )
        texture_engine = TextureEngine()
        texture_engine.load()
        job_store.update(
            job_id, progress=85, stage="applying_pbr", message="Applying PBR textures"
        )
        texture_engine.apply_pbr(mesh_path, glb_path, texture_dir)
        texture_engine.unload()
        del texture_engine
        purge_cuda_memory()

        job_store.update(
            job_id,
            status="complete",
            progress=100,
            stage="complete",
            message="3D model is ready",
            output_glb_path=str(glb_path),
        )
    except Exception as exc:
        purge_cuda_memory()
        job_store.update(
            job_id,
            status="failed",
            stage="failed",
            message="Generation failed",
            error=str(exc),
        )
