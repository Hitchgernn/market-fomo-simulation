from pathlib import Path

html = Path("frontend/index.html").read_text()

required_snippets = {
    "terminal shell scrollable viewport": ".terminal-shell {\n        display: grid;\n        grid-template-rows: auto minmax(0, 1fr);\n        gap: calc(var(--grid) * 2);\n        min-height: 100vh;",
    "dashboard fixed rows": ".dashboard-grid {\n        display: grid;\n        grid-template-columns: minmax(320px, 0.95fr) minmax(420px, 1.45fr) minmax(320px, 0.95fr);\n        grid-template-rows: minmax(0, 38vh) minmax(0, 220px) minmax(0, 1fr);",
    "event panel clips overflow": ".event-panel {\n        grid-area: events;\n        display: grid;\n        grid-template-rows: auto minmax(0, 1fr);\n        min-height: 0;\n        overflow: hidden;",
    "chat panel clips overflow": ".chat-panel {\n        grid-area: chat;\n        display: grid;\n        grid-template-rows: auto minmax(0, 1fr);\n        min-height: 0;\n        overflow: hidden;",
    "stable scrollbar gutter": "scrollbar-gutter: stable;",
}

missing = [name for name, snippet in required_snippets.items() if snippet not in html]
if "overflow: hidden;\n        padding: calc(var(--grid) * 2);" in html:
    missing.append("terminal shell must allow page scroll")
if missing:
    raise SystemExit("missing layout safeguards: " + ", ".join(missing))
print("layout css safeguards ok")
