from pathlib import Path

source = Path("frontend/sketch.js").read_text()

required = [
    'const LOCAL_API_BASE = "http://localhost:8000";',
    'const PROD_API_BASE = window.FOMO_API_BASE || window.location.origin;',
    'const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" ? LOCAL_API_BASE : PROD_API_BASE;',
]

missing = [snippet for snippet in required if snippet not in source]
if missing:
    raise SystemExit("missing API base auto-detect config")
print("api base config ok")
