"""Static validation for Legion-OSINT; does not need credentials or network access."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []

for path in (ROOT / "app").glob("*.py"):
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        errors.append(f"Python syntax error in {path.relative_to(ROOT)}: {exc}")

for relative in ("config/channels.json", "config/keywords.json", "config/source_registry.json",
                 "config/source_discovery_queue.json"):
    path = ROOT / relative
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid JSON in {relative}: {exc}")

if errors:
    for error in errors:
        print("FAIL:", error)
    raise SystemExit(1)

print("PASS: Python syntax and JSON configuration files are valid.")
