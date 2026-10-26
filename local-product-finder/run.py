import os
from pathlib import Path

# Load .env file manually if exists
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")
    
    print("=" * 60)
    print("   LOCAL PRODUCT FINDER - Web Server Running")
    print("=" * 60)
    print(f" -> URL: http://{host}:{port}")
    print(" -> Customer Mode: Search & browse freely without an account")
    print(" -> Shop Owner Mode: Use 1-Click demo logins on /auth/login")
    print("    Demo account 1: greenvalley@localfinder.demo (Pass: DemoPass123!)")
    print("    Demo account 2: cornerstone@localfinder.demo (Pass: DemoPass123!)")
    print("=" * 60)

    app.run(host=host, port=port, debug=True)
