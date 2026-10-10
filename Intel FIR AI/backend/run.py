import uvicorn
import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"\n=======================================================")
    print(f"  SMART FIR 360 - BNSS Section 173 Platform")
    print(f"  API & UI Server starting at: http://{host}:{port}")
    print(f"  Swagger API Docs: http://{host}:{port}/docs")
    print(f"=======================================================\n")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
