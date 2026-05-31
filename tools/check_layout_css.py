from pathlib import Path

html = Path("frontend/index.html").read_text()

required_snippets = {
    "terminal shell fixed desktop canvas": ".terminal-shell {\n        display: grid;\n        grid-template-rows: auto minmax(0, 1fr);\n        gap: calc(var(--grid) * 2);\n        width: 1920px;\n        min-height: 1080px;",
    "dashboard fixed desktop rows": ".dashboard-grid {\n        display: grid;\n        grid-template-columns: 525px 802px 525px;\n        grid-template-rows: 352px 242px 1fr;",
    "event panel clips overflow": ".event-panel {\n        grid-area: events;\n        display: grid;\n        grid-template-rows: auto minmax(0, 1fr);\n        min-height: 0;\n        overflow: hidden;",
    "chat panel clips overflow": ".chat-panel {\n        grid-area: chat;\n        display: grid;\n        grid-template-rows: auto minmax(0, 1fr);\n        min-height: 0;\n        overflow: hidden;",
    "stable scrollbar gutter": "scrollbar-gutter: stable;",
}

missing = [name for name, snippet in required_snippets.items() if snippet not in html]
if "@media (max-width: 1240px)" in html or "@media (max-width: 900px)" in html:
    missing.append("desktop layout must not shrink at smaller browser widths")
if "overflow: hidden;\n        padding: calc(var(--grid) * 2);" in html:
    missing.append("terminal shell must allow page scroll")
if missing:
    raise SystemExit("missing layout safeguards: " + ", ".join(missing))
print("layout css safeguards ok")
