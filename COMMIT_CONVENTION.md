# Commit Convention Guide

Always follow **Conventional Commits** when committing any change. No exceptions.
ALWAYS commit after big changes you made
---

## Format

```
<type>(<scope>): <message>
```

- **type** — what kind of change
- **scope** — which file, module, or area was changed (keep it short)
- **message** — short, lowercase, imperative tense ("add" not "added")

---

## Types

| Type | When to use |
|------|-------------|
| `feat` | Adding a new feature or capability |
| `fix` | Fixing a bug or broken behavior |
| `refactor` | Restructuring code without changing behavior |
| `chore` | Setup, config, dependencies, tooling |
| `style` | Formatting, spacing, naming (no logic change) |
| `docs` | Adding or updating documentation / comments |
| `test` | Adding or updating tests |
| `perf` | Performance improvement |
| `remove` | Deleting files, functions, or dead code |

---

## Scope Examples

Use the filename, module, or layer — keep it one word or hyphenated.

```
feat(scraper): add bright data web scraper api integration
fix(normalizer): handle empty job title edge case
refactor(db): restructure job posting schema
chore(env): add bright data api key to env template
style(dashboard): clean up spacing on heatmap component
docs(readme): add setup instructions for bright data
feat(api): add /trends endpoint for emerging titles
fix(claude-api): retry on rate limit error
perf(analyzer): batch title embedding computation
remove(scraper): drop unused indeed direct scraper
```

---

## Rules

1. **Always lowercase** — type, scope, and message
2. **No period at the end** of the message
3. **Be specific** with scope — `fix(scraper)` not `fix(code)`
4. **One concern per commit** — don't bundle unrelated changes
5. **Imperative mood** — "add", "fix", "update", not "added", "fixed", "updated"
6. **Keep message under 72 characters**

---

## Multi-line Commit (when needed)

For bigger changes, add a body after a blank line:

```
feat(analyzer): add spread velocity scoring

Calculates how fast a job title spreads across companies.
Uses a 30-day rolling window. Outputs a score from 0–100.
```

---

## What NOT to do

```bash
# ❌ Bad
git commit -m "fix stuff"
git commit -m "WIP"
git commit -m "updated files"
git commit -m "feat: Added the scraper and also fixed the DB and cleaned up CSS"

# ✅ Good
git commit -m "fix(normalizer): handle null title from linkedin scraper"
git commit -m "feat(scraper): integrate bright data serp api for job discovery"
```
