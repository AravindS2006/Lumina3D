# Lumina3D

Lumina3D is a video-to-3D reconstruction platform with a React frontend and a FastAPI backend designed for Colab GPU execution.

## Runtime Notes

- The backend is configured for non-commercial usage workflows.
- The pipeline attempts real Hunyuan model inference and tracks runtime tier/fallback details in `GET /status/{job_id}`.
- Recommended profile on free Colab is `balanced`.

## Run Backend in Colab / VS Code Notebook

1. Open `backend/Lumina3D_Colab_Server.ipynb`.
2. Run all cells top to bottom.
3. Paste your `NGROK_AUTHTOKEN` in the environment cell.
4. Keep the Uvicorn cell running.

The notebook launches FastAPI locally and creates a fresh ngrok URL for each session.

Before first generate call, run runtime diagnostics:

- `GET /debug/runtime`

This endpoint reports model import readiness for `hy3dgen`/`hy3dpaint` modules.

### Quick API checks

The API now responds at root `/` with service metadata. Useful paths:

- Root: `<ngrok-url>/`
- Health: `<ngrok-url>/healthz`
- Docs: `<ngrok-url>/docs`
- Runtime probe: `<ngrok-url>/debug/runtime`
- Generate: `<ngrok-url>/generate`
- Status: `<ngrok-url>/status/<job_id>`
- Download: `<ngrok-url>/download/<job_id>`

`POST /generate` accepts optional form fields:

- `profile`: `balanced` (default), `low_vram`, `quality`
- `view_labels`: JSON map for image view assignment (`front/left/back/right`)

## Run Frontend Locally

1. Copy `frontend/.env.example` to `frontend/.env`.
2. Set `VITE_API_BASE_URL` to your backend ngrok URL.
3. Install and run:

```bash
cd frontend
npm install
npm run dev
```

The Axios client already sends:

- `ngrok-skip-browser-warning: 69420`

Model preview in the UI is loaded from a blob response, while download is handled by a dedicated button.

### 404 troubleshooting

If frontend shows `Request failed with status code 404`:

1. Verify backend health at `<base-url>/healthz` (must be `200`).
2. Verify endpoint methods:
   - `GET <base-url>/generate` should return `405` (method exists).
   - `POST <base-url>/generate` should be used by frontend.
3. Ensure `frontend/.env` has no stale URL and restart dev server after editing.

If `/debug/runtime` is 404 but `/healthz` is 200, you are running an older backend build.
Restart backend from latest source so `/healthz` includes `runtime_probe: true`.

If this keeps happening in VS Code notebooks, ensure stale servers on port `8000` are killed before restart.
The provided Colab notebook handles this automatically.

For Colab runtime, your local unpushed changes are not used automatically. Push your latest repository
changes to remote first, then rerun notebook repo-sync cells.

## Pipeline Profiles

- `balanced`: reliability-first profile for free Colab T4
- `low_vram`: reduced settings for unstable/low-memory sessions
- `quality`: higher quality, slower and higher VRAM pressure
