"""Validate the TBC import package's JSON shape and Python-compatible TPY syntax."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "tbc" / "legion_osint_tbc_import.json"


def main():
    data = json.loads(PACKAGE.read_text(encoding="utf-8"))
    commands = data.get("commands")
    if not isinstance(commands, list) or len(commands) < 20:
        raise SystemExit("TBC package must contain at least 20 commands.")
    names = [item.get("command") for item in commands]
    if len(names) != len(set(names)):
        raise SystemExit("Duplicate TBC command names detected.")
    required = {
        ".env", "myid", "start", "help", "status", "daily", "bangladesh",
        "search", "leads", "briefs", "coverage", "report", "reviewqueue",
        "reviewlead", "candidates", "incidentdraft", "incidentqueue",
        "approveincident", "linklead", "ask", "research", "digest", "alerts_on",
        "alerts_off", "alert_poll"
    }
    missing = required.difference(names)
    if missing:
        raise SystemExit("Missing TBC commands: " + ", ".join(sorted(missing)))

    for item in commands:
        name, code = item["command"], item["code"]
        if name == ".env":
            if "OWNER_IDS = []" not in code or "FEED_URL" not in code:
                raise SystemExit("The .env command must retain safe owner/feed placeholders.")
            continue
        compile(code, f"<tbc:{name}>", "exec")
        lowered = code.lower()
        for forbidden in ("eval(", "exec(", "subprocess", "os.system", "open("):
            if forbidden in lowered:
                raise SystemExit(f"Unsafe construct {forbidden!r} found in /{name}.")
    print(f"Validated {len(commands)} TBC commands: JSON shape and Python-compatible syntax passed.")


if __name__ == "__main__":
    main()
