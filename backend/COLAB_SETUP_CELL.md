# Lumina3D Colab Setup Cell

Prefer using `backend/Lumina3D_Colab_Server.ipynb` if you are running through the VS Code Colab/Jupyter extension.
It includes dependency install, repo sync, environment setup, robust uvicorn launch (`--app-dir`), and ngrok verification.

Important: the notebook now force-cleans any stale process bound to port `8000` before launching backend,
to avoid accidentally hitting an older server build.

```python
!pip install -U fastapi "uvicorn[standard]" python-multipart pyngrok opencv-python torch transformers diffusers accelerate bitsandbytes trimesh Pillow huggingface-hub einops omegaconf
```

Optional launch flow after install:

```python
import os

os.environ["NGROK_AUTHTOKEN"] = "<your-token>"
os.environ["ENABLE_NGROK"] = "0"
os.environ["CORS_ALLOW_ORIGINS"] = "http://localhost:5173"

!uvicorn --app-dir /content/Lumina3D/backend app.main:app --host 0.0.0.0 --port 8000
```

Recommended for free Colab reliability:

```python
from pyngrok import ngrok
import os

ngrok.kill()
ngrok.set_auth_token(os.environ["NGROK_AUTHTOKEN"])
tunnel = ngrok.connect(8000, bind_tls=True)
print("VITE_API_BASE_URL=" + tunnel.public_url)
```

Runtime readiness probe:

```python
import requests
print(requests.get("http://127.0.0.1:8000/debug/runtime", timeout=20).json())
```
