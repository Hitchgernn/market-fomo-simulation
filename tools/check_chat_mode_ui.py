from pathlib import Path

html = Path("frontend/index.html").read_text()
js = Path("frontend/sketch.js").read_text()

required_html = [
    'class="chat-mode-toggle"',
    'class="chat-mode-option"',
    'id="chat-mode-scripted"',
    'id="chat-mode-ai"',
]
required_js = [
    'const SCRIPTED_CHAT_INTERVAL_MS = 2000;',
    'let scriptedChatTimer = null;',
    'chatMode: document.getElementById("chat-mode-ai").checked ? "ai" : "scripted",',
    'document.getElementById("chat-mode-scripted").checked = config.chatMode !== "ai";',
    'document.getElementById("chat-mode-ai").checked = config.chatMode === "ai";',
    'startScriptedChatTimer();',
    'setInterval(addScriptedChatMessage, SCRIPTED_CHAT_INTERVAL_MS);',
    'function addScriptedChatMessage()',
    'document.getElementById("chat-mode-ai").checked || !isRunning || !lastPayload',
    'while (feed.children.length > 40)',
]
forbidden_js = [
    'localStorage',
    'sessionStorage',
    'indexedDB',
]
missing = [item for item in required_html if item not in html]
missing.extend(item for item in required_js if item not in js)
missing.extend(f"forbidden persistent cache: {item}" for item in forbidden_js if item in js)
if missing:
    raise SystemExit("missing chat mode UI wiring: " + ", ".join(missing))
print("chat mode UI ok")
