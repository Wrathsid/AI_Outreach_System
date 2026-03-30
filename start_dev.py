import subprocess
import sys
import os
import signal
import time

def start_dev():
    """Starts the backend and frontend development servers for AI Outreach System."""
    root = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Resolve Python executable (prefer .venv)
    venv_dir = os.path.join(root, ".venv")
    if os.path.exists(venv_dir):
        if os.name == "nt":  # Windows
            python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
        else:  # Mac/Linux
            python_exe = os.path.join(venv_dir, "bin", "python")
    else:
        python_exe = sys.executable

    print("\n" + "="*50)
    print(" 🚀 STARTING AI OUTREACH SYSTEM DEV ENVIRONMENT")
    print("="*50)
    print(f"📂 Root:   {root}")
    print(f"🐍 Python: {python_exe}")
    
    # 2. Start Backend (FastAPI)
    print("\n📡 Starting Backend (FastAPI)...")
    backend_proc = subprocess.Popen(
        [python_exe, "-m", "backend.main"],
        cwd=root,
        bufsize=1,
        universal_newlines=True
    )
    
    # 3. Start Frontend (Next.js)
    print("🎨 Starting Frontend (Next.js)...")
    frontend_dir = os.path.join(root, "frontend")
    
    # Check if npm is available
    try:
        frontend_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            shell=True if os.name == "nt" else False
        )
    except FileNotFoundError:
        print("❌ Error: 'npm' not found. Please ensure Node.js is installed.")
        backend_proc.terminate()
        return

    print("\n" + "-"*50)
    print("✅ SERVERS RUNNING")
    print("   • Backend:  http://localhost:8000")
    print("   • Frontend: http://localhost:3000")
    print("   • Docs:     http://localhost:8000/docs")
    print("-"*50)
    print("💡 Press Ctrl+C to stop both servers.")
    print("="*50 + "\n")

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
            # Check if processes are still alive
            if backend_proc.poll() is not None:
                print("\n⚠️ Backend process exited.")
                break
            if frontend_proc.poll() is not None:
                print("\n⚠️ Frontend process exited.")
                break
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down servers...")
    finally:
        # Cleanup
        if backend_proc.poll() is None:
            backend_proc.terminate()
        if frontend_proc.poll() is None:
            frontend_proc.terminate()
            
        backend_proc.wait()
        frontend_proc.wait()
        print("✨ Cleaned up. Have a great day!")

if __name__ == "__main__":
    start_dev()
