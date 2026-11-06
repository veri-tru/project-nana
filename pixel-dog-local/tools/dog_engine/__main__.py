"""One entry point for state, integrity checks, head rendering and body tools."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["status", "doctor", "verify", "head", "body", "pixel-diagnostic"])
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    rest = args.args[1:] if args.args[:1] == ["--"] else args.args
    if args.command in ("status", "doctor", "verify") and rest:
        parser.error("This command does not take additional arguments")
    try:
        if args.command in ("status", "doctor"):
            from . import state
            result = state.current() if args.command == "status" else state.doctor()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1 if result.get("problems") else 0
        if args.command == "head":
            from . import head
            head.main(rest)
            return 0
        if args.command == "body":
            return subprocess.call([sys.executable, str(ROOT / "tools/static_maker/render_v03.py"), *rest], cwd=ROOT)
        if args.command == "pixel-diagnostic":
            return subprocess.call([sys.executable, "-m", "tools.dog_engine.pixel", "--diagnostic", *rest], cwd=ROOT)
        if args.command == "verify":
            failed = False
            for suite in ("tools/head_engine/tests", "tools/static_maker/tests", "tools/dog_engine/tests"):
                result = subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", suite, "-q"], cwd=ROOT)
                failed = failed or result != 0
            return int(failed)
    except (OSError, ValueError, KeyError, ImportError) as exc:
        parser.exit(2, f"dog_engine: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
