"""Static validation for Legion-OSINT; does not need credentials or network access."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []

for folder in ("app", "scripts"):
    for path in (ROOT / folder).glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"Python syntax error in {path.relative_to(ROOT)}: {exc}")

for relative in ("config/channels.json", "config/keywords.json", "discovery/seed_candidates.json", "config/source_registry.json",
                 "config/source_discovery_queue.json", "config/research.json", "config/news_sources.json"):
    path = ROOT / relative
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid JSON in {relative}: {exc}")

try:
    seed_data = json.loads((ROOT / "discovery/seed_candidates.json").read_text(encoding="utf-8"))
    seed_candidates = seed_data.get("candidates", [])
    seed_usernames = [item.get("username", "").lower() for item in seed_candidates]
    if len(seed_usernames) != len(set(seed_usernames)):
        errors.append("Duplicate usernames in discovery/seed_candidates.json")
    for item in seed_candidates:
        if not item.get("username") or not item.get("region") or not item.get("language"):
            errors.append("Seed candidate missing username, region or language")
        if item.get("review_status", "UNREVIEWED_CANDIDATE") != "UNREVIEWED_CANDIDATE":
            errors.append(f"Seed candidate @{item.get('username')} must remain unreviewed in the seed file")
        if item.get("enabled_for_collection", False):
            errors.append(f"Seed candidate @{item.get('username')} must not be enabled from the seed file")
except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
    errors.append(f"Invalid discovery seed registry: {exc}")

try:
    channels = json.loads((ROOT / "config/channels.json").read_text(encoding="utf-8"))["channels"]
    usernames = [item["username"].lower() for item in channels]
    allowed_classes = {"unknown", "unofficial", "independent_media", "civil_society",
                       "official_media", "official_government", "intergovernmental",
                       "research_academic", "other"}
    if len(usernames) != len(set(usernames)):
        errors.append("Duplicate Telegram usernames in config/channels.json")
    for item in channels:
        if item.get("source_class", "unknown") not in allowed_classes:
            errors.append(f"Unsupported source_class for @{item.get('username')}")
        for required in ("username", "priority", "language", "source_type", "source_affiliation"):
            if not item.get(required):
                errors.append(f"Missing {required} for Telegram channel entry")
except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
    errors.append(f"Invalid Telegram source registry: {exc}")

try:
    news_sources = json.loads((ROOT / "config/news_sources.json").read_text(encoding="utf-8"))["sources"]
    source_ids = [item["source_id"] for item in news_sources]
    if len(source_ids) != len(set(source_ids)):
        errors.append("Duplicate source_id values in config/news_sources.json")
    for item in news_sources:
        if not item.get("publisher_name") or not item.get("feed_url", "").startswith("https://"):
            errors.append(f"Invalid public RSS source entry: {item.get('source_id', 'unknown')}")
except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
    errors.append(f"Invalid RSS source registry: {exc}")

# Validate the manually deployed TBC V8 summary command as Python-compatible syntax.
summary_command = ROOT / "tbc" / "summary_v8_command.txt"
try:
    command_text = summary_command.read_text(encoding="utf-8")
    command_tree = ast.parse(command_text, filename=str(summary_command))
    if any(isinstance(node, ast.While) for node in ast.walk(command_tree)):
        errors.append("TBC V8 summary command must not contain while loops")
    for required in ("Bangladesh relevant source posts:", "EXACT-TEXT GROUP:", "SEVEN-DAY TEMPORAL COMPARISON"):
        if required not in command_text:
            errors.append(f"TBC V8 summary command missing required output: {required}")
except (OSError, SyntaxError) as exc:
    errors.append(f"Invalid TBC V8 summary command: {exc}")

if errors:
    for error in errors:
        print("FAIL:", error)
    raise SystemExit(1)

print("PASS: Python syntax and JSON configuration files are valid.")
