"""Keep release proposals tied to the pinned upstream source identity."""

import argparse
import json
from pathlib import Path
import re

from python.runfiles import runfiles


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--upstream-package", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--snapshot", action="store_true")
    args = parser.parse_args()
    files = runfiles.Create()
    config = json.loads(Path(files.Rlocation(args.config)).read_text())
    package = json.loads(Path(files.Rlocation(args.upstream_package)).read_text())

    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        raise ValueError("Hermes source pin must be a full commit hash")

    # Upstream version-utils.js uses hermes-compiler's version plus nine hash chars.
    expected = package["version"]
    if args.snapshot:
        expected += "-" + args.commit[:9]

    release = config["packages"]["."]
    proposed = release["release-as"]
    if not re.fullmatch(re.escape(expected) + r"(?:\.bcr\.[1-9][0-9]*)?", proposed):
        raise ValueError(
            f"release-as must be {expected}, optionally followed by .bcr.N"
        )
    if release.get("prerelease", False) != ("-" in expected):
        raise ValueError("Snapshot releases must retain prerelease status")

    print(f"Release proposal matches pinned Hermes: {proposed}")


if __name__ == "__main__":
    main()
