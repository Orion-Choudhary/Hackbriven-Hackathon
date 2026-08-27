from pathlib import Path
import os

env_path = Path(__file__).resolve().parents[2] / ".env"
if env_path.is_file():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip("'\"")
            if k and k not in os.environ:
                os.environ[k] = v
