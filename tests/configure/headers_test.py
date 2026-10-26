"""Keep all target headers byte-identical to the previous configuration tool."""

import argparse
import hashlib
import json
from pathlib import Path

from python.runfiles import runfiles


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--header", action="append", required=True)
    args = parser.parse_args()
    files = runfiles.Create()
    expected = json.loads(Path(files.Rlocation(args.expected)).read_text())
    actual = {}
    for header in args.header:
        name, path = header.split("=", 1)
        actual[name] = hashlib.sha256(Path(files.Rlocation(path)).read_bytes()).hexdigest()
    if actual != expected:
        changed = sorted(name for name in actual.keys() | expected.keys() if actual.get(name) != expected.get(name))
        raise ValueError(f"Configuration headers changed: {changed}")
    print("All 12 target headers match previous output")


if __name__ == "__main__":
    main()
