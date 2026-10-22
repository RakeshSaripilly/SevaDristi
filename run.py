#!/usr/bin/env python3
"""
SevaDristi — Single Command Application Launcher
Runs both the FastAPI backend (port 8000) and the Vite React frontend (port 5173) concurrently.
Handles graceful shutdown of both servers on Ctrl+C.
"""

import sys
import os
import subprocess
import signal
import time
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"

import socket

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def check_existing_services():
    backend_busy = is_port_in_use(8000)
    frontend_busy = is_port_in_use(5173)

    if backend_busy or frontend_busy:
        print("\n [!] Notice: One or more services are ALREADY RUNNING on your system:")
        if backend_busy:
            print("     * Port 8000 (Backend) is already active.")
        if frontend_busy:
            print("     * Port 5173 (Frontend) is already active.")
        print("\n [i] You can already access SevaDristi directly in your browser:")
        print("     -> http://127.0.0.1:5173\n")
        print(" To restart services, first terminate the existing processes:")
        print("     powershell: Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000,5173).OwningProcess -Force\n")
        return False
    return True

def print_banner():
    banner = r"""
  =============================================================
     ____                 ____       _     _   _ 
    / ___|  _____   ____ |  _ \ _ __(_)___| |_(_)
    \___ \ / _ \ \ / / _` | | | | '__| / __| __| |
     ___) |  __/\ V / (_| | |_| | |  | \__ \ |_| |
    |____/ \___| \_/ \__,_|____/|_|  |_|___/\__|_|
    
    Offline-Capable Multilingual Pre-Verification Assistant
    Telangana MeeSeva & CSC Service Centres
  =============================================================
    """
    print(banner)
    print(" [✓] Starting FastAPI backend on http://127.0.0.1:8000 ...")
    print(" [✓] Starting Vite React frontend on http://127.0.0.1:5173 ...")
    print(" [i] Press Ctrl+C at any time to gracefully stop both servers.\n")

def main():
    if not check_existing_services():
        sys.exit(0)

    print_banner()

    # Determine command executables
    python_exe = sys.executable
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    # Start FastAPI backend process
    backend_cmd = [
        python_exe,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000"
    ]
    
    # Start Vite frontend process
    frontend_cmd = [
        npm_cmd,
        "run",
        "dev",
        "--",
        "--host",
        "127.0.0.1",
        "--port",
        "5173"
    ]

    backend_proc = None
    frontend_proc = None

    try:
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(ROOT_DIR),
            stdout=sys.stdout,
            stderr=sys.stderr
        )

        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=str(FRONTEND_DIR),
            stdout=sys.stdout,
            stderr=sys.stderr
        )

        # Give servers a few seconds to start, then notify
        time.sleep(2)
        print("\n [✓] SevaDristi is running live!")
        print("     - Citizen & Volunteer UI: http://127.0.0.1:5173")
        print("     - CSC Operator Desktop:   http://127.0.0.1:5173 (click Operator view)")
        print("     - API Documentation:      http://127.0.0.1:8000/docs")
        print("     - Health Status:          http://127.0.0.1:8000/api/health\n")

        # Keep parent alive and monitor child processes
        while True:
            time.sleep(0.5)
            if backend_proc.poll() is not None:
                print("\n[!] Backend process exited.")
                break
            if frontend_proc.poll() is not None:
                print("\n[!] Frontend process exited.")
                break

    except KeyboardInterrupt:
        print("\n[*] Stopping SevaDristi services...")
    finally:
        # Gracefully terminate both processes
        for proc, name in [(backend_proc, "Backend"), (frontend_proc, "Frontend")]:
            if proc and proc.poll() is None:
                try:
                    if sys.platform == "win32":
                        proc.terminate()
                    else:
                        proc.send_signal(signal.SIGTERM)
                    proc.wait(timeout=3)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
        print("[✓] All services stopped cleanly. Goodbye!\n")

if __name__ == "__main__":
    main()
