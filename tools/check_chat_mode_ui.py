from pathlib import Path

html = Path("frontend/index.html").read_text()
js = Path("frontend/sketch.js").read_text()

required_html = [
    'id="chat-mode-scripted"',
    'id="chat-mode-ai"',
]
required_js = [
    'chatMode: document.getElementById("chat-mode-ai").checked ? "ai" : "scripted",',
    'document.getElementById("chat-mode-scripted").checked = config.chatMode !== "ai";',
    'document.getElementById("chat-mode-ai").checked = config.chatMode === "ai";',
]
missing = [item for item in required_html if item not in html]
missing.extend(item for item in required_js if item not in js)
if missing:
    raise SystemExit("missing chat mode UI wiring")
print("chat mode UI ok")
