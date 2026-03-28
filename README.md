# Lumina3D

Lumina3D is a video-to-3D reconstruction platform with a React frontend and a FastAPI backend designed for Colab GPU execution.

## Run Backend in Colab / VS Code Notebook

1. Open `backend/Lumina3D_Colab_Server.ipynb`.
2. Run all cells top to bottom.
3. Paste your `NGROK_AUTHTOKEN` in the environment cell.
4. Keep the Uvicorn cell running.

The notebook launches FastAPI and exposes it with ngrok when enabled.

### Quick API checks

If opening the raw ngrok root URL shows `{"detail":"Not Found"}`, that is expected because no `/` route is defined.
Use these paths instead:

- Health: `<ngrok-url>/healthz`
- Generate: `<ngrok-url>/generate`
- Status: `<ngrok-url>/status/<job_id>`
- Download: `<ngrok-url>/download/<job_id>`

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
