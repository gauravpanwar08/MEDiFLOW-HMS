import os
import signal
import subprocess
import sys
import time

# Ensure frontend/node_modules symlink exists to root node_modules
if not os.path.exists("frontend/node_modules") and os.path.exists("node_modules"):
    try:
        os.symlink("../node_modules", "frontend/node_modules")
    except Exception:
        pass

# Ensure database is initialized and seeded
try:
    subprocess.run([sys.executable, "backend/seed.py"], check=False)
except Exception:
    pass

backend_cmd = [
    sys.executable, "-m", "uvicorn", "app.main:app",
    "--app-dir", "backend",
    "--host", "127.0.0.1",
    "--port", "8001"
]

frontend_cmd = [
    "node_modules/.bin/vite", "frontend",
    "--port", "3000",
    "--host", "0.0.0.0"
]

backend_proc = subprocess.Popen(backend_cmd)
frontend_proc = subprocess.Popen(frontend_cmd)

def handle_signal(sig, frame):
    backend_proc.terminate()
    frontend_proc.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

try:
    while True:
        time.sleep(1)
        if backend_proc.poll() is not None:
            backend_proc = subprocess.Popen(backend_cmd)
        if frontend_proc.poll() is not None:
            time.sleep(2)
            frontend_proc = subprocess.Popen(frontend_cmd)
except Exception:
    pass
finally:
    backend_proc.terminate()
    frontend_proc.terminate()
