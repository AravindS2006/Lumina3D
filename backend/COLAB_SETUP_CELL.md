# Lumina3D Colab Setup Cell

Prefer using `backend/Lumina3D_Colab_Server.ipynb` if you are running through the VS Code Colab/Jupyter extension.
It includes dependency install, environment setup, and API launch cells.

```python
!pip install -U fastapi "uvicorn[standard]" python-multipart pyngrok opencv-python torch transformers diffusers accelerate bitsandbytes trimesh Pillow
```

Optional launch flow after install:

```python
import os

os.environ["NGROK_AUTHTOKEN"] = "<your-token>"
os.environ["ENABLE_NGROK"] = "1"
os.environ["CORS_ALLOW_ORIGINS"] = "http://localhost:5173"

!uvicorn app.main:app --host 0.0.0.0 --port 8000
```
