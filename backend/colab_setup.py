"""Lumina3D Colab one-cell setup helper.

Usage in Colab:
!python colab_setup.py
"""

from __future__ import annotations

import subprocess
import sys


def main() -> None:
    packages = [
        "fastapi",
        "uvicorn[standard]",
        "python-multipart",
        "pyngrok",
        "opencv-python",
        "torch",
        "transformers",
        "diffusers",
        "accelerate",
        "bitsandbytes",
        "trimesh",
        "Pillow",
    ]
    cmd = [sys.executable, "-m", "pip", "install", "-U", *packages]
    subprocess.run(cmd, check=True)
    print("Lumina3D setup complete")


if __name__ == "__main__":
    main()
