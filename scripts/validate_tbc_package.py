"""Validate the TBC import package's JSON shape and Python-compatible TPY syntax."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "tbc" / "legion_osint_tbc_import.json"
TXT_PACKAGE = ROOT / "tbc" / "legion_osint_tbc_import.txt"


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

    parsed_txt = []
    txt_lines = TXT_PACKAGE.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(txt_lines):
        if not txt_lines[index].strip():
            index += 1
            continue
        if not txt_lines[index].startswith("Command: "):
            raise SystemExit("Unexpected line in TBC TXT import package.")
        name = txt_lines[index][9:].strip()
        if index + 1 >= len(txt_lines) or txt_lines[index + 1] != "---":
            raise SystemExit("Missing opening command fence in TBC TXT package.")
        index += 2
        code_lines = []
        while index < len(txt_lines) and txt_lines[index] != "---":
            code_lines.append(txt_lines[index])
            index += 1
        if index >= len(txt_lines):
            raise SystemExit("Missing closing command fence in TBC TXT package.")
        parsed_txt.append({"command": name, "code": "\\n".join(code_lines)})
        index += 1
    if parsed_txt != commands:
        raise SystemExit("JSON and TXT TBC import packages do not match.")

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
