# Pixel Trading Terminal Redesign

## Goal

Redesign only the frontend presentation layer of FOMO Market Simulation into a pixel-style market dashboard. Keep the app recognizable as a trading/market simulation so instructors can understand it quickly.

## Chosen direction

Use a cyberpunk pixel-noir trading terminal, not a game cockpit. Pixel styling comes from the visual system: hard grid, square panels, offset shadows, pixel fonts, neon palette, scanline/background assets, pixel icons, and press-state controls.

## Non-goals

- Do not change backend endpoints, data models, or simulation logic.
- Do not rename core concepts: keep `Graph`, `Live Market`, `Order Book`, `Controls`, `Market Events`, and `Market Chat`.
- Do not pixelize the Mesa graph itself. It must stay readable as a network graph.
- Do not turn the interface into an arcade/RPG game UI.

## Layout

Use a trading-first dashboard layout:

1. Top stat strip for `Price`, `Imbalance`, `Neutral`, `Aware`, `Panic`, and `Regime`.
2. Main content row split into three zones:
   - Left: square `Graph` panel for the Mesa network graph.
   - Center: wider rectangular `Live Market` chart panel so price/candlestick data is clearly visible.
   - Right: stacked `Controls`, `Market Events`, and `Market Chat` panels.
3. Bottom `Order Book` strip for buy volume, sell volume, upper/lower limits, and limit state.

On mobile, stack panels vertically in the same semantic order: stat strip, `Graph`, `Live Market`, `Controls`, `Order Book`, events, chat.

## Visual system

- Base grid: 8px spacing. All margins, gaps, padding, and panel sizes should use 8px multiples.
- Corners: 0px radius.
- Panel border: 3-4px solid neon color.
- Panel shadow: `4px 4px 0 #000` or `8px 8px 0 #000`.
- Palette: dark navy/black base plus cyan, mint, magenta, yellow, red, violet, and muted text.
- Typography: online pixel font for headings via Google Fonts or similar; monospace body for readability.
- Assets: online fonts/icons/background patterns are allowed. Use them for pixel atmosphere, not for core graph rendering.
- Motion: subtle scanline scroll, blinking live indicator, button press translation. Avoid distracting animation.

## Components

- Pixel panel: square trading widget with title bar, neon border, black offset shadow.
- Pixel button: square, neon border, offset shadow, `translate(2px, 2px)` active state.
- Pixel input: square field, clear label, visible keyboard focus outline.
- Pixel badge/stat: compact 8px-grid metric tile.
- Pixel progress/stat bar: use for volume share, price band, and limit state.
- Pixel dialog/error: for backend offline or reset failure, show terminal-style warning while keeping current labels.
- Pixel loader: small stepped block/spinner while fetching state.

## Data and integration

Use existing frontend API calls:

- `GET /state` for initial state.
- `GET /tick` for polling/step.
- `POST /reset` for controls.

Keep all payload fields and backend behavior unchanged. Existing p5.js network graph should continue rendering `payload.nodes`. Existing Chart.js live chart should remain, but restyle it for pixel terminal visuals and correct candlestick/line readability.

## UX behavior

- Preserve existing actions: `Run/Pause`, `Step`, `Apply`, `FOMO Pump`, `Maker Dump`, `Lower Limit Spiral`.
- Preserve all current controls and validation behavior.
- Keep `Graph` square-ish and readable.
- Make `Live Market` wider than `Graph`, with upright candlestick/price marks and clear axes.
- Use online pixel assets sparingly for polish: fonts, small icons, background grid/scanline texture.

## Accessibility

- Keep semantic section labels and ARIA labels.
- Maintain keyboard navigation for controls.
- Use visible pixel-style focus indicators.
- Keep body text readable; use pixel font mainly for headings/buttons/labels.
- Maintain sufficient contrast on neon-on-dark palette.

## Testing

- Run backend compile check: `python -m compileall backend`.
- Run frontend syntax check: `node --check frontend/sketch.js`.
- Start backend and frontend.
- Manually verify: initial state, running polling, pause/run, step, apply/reset, all presets, offline error state, graph rendering, chart rendering, events, chat, mobile stacking.
