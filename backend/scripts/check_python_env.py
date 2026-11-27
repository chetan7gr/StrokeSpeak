import sys
import subprocess
from pathlib import Path

def check_env():
    print(f"PYTHON_EXECUTABLE: {sys.executable}")
    print(f"PYTHON_VERSION: {sys.version.split()[0]}")
    
    # Read pyvenv.cfg
    pyvenv_path = Path(__file__).resolve().parents[1] / ".venv" / "pyvenv.cfg"
    home_dir = None
    if pyvenv_path.exists():
        with open(pyvenv_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("home") or line.startswith("version"):
                    print(f"PYVENV_CFG: {line.strip()}")
                    if line.startswith("home"):
                        home_dir = line.split("=", 1)[1].strip()
        if home_dir:
            home_exists = Path(home_dir).exists()
            print(f"HOME_FOLDER_EXISTS: {home_exists} ({home_dir})")
    else:
        print("pyvenv.cfg NOT FOUND")
        
    # Check imports
    for pkg in ["fastapi", "uvicorn", "pydantic", "mysql.connector"]:
        try:
            mod = __import__(pkg)
            ver = getattr(mod, "__version__", "unknown")
            print(f"IMPORT_SUCCESS: {pkg} == {ver}")
        except Exception as e:
            print(f"IMPORT_FAILED: {pkg} -> {e}")

if __name__ == "__main__":
    check_env()
