"""Copy a checked-in Hermes entry into a registry checkout."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9][0-9A-Za-z.+-]*", args.version):
        raise ValueError("Invalid release version")
    root = Path(os.environ["BUILD_WORKSPACE_DIRECTORY"])
    source = root / "bcr/modules/hermes"
    target = args.registry / "modules/hermes"
    metadata = json.loads((source / "metadata.json").read_text())
    if args.version not in metadata["versions"]:
        raise ValueError("Release version has no checked-in BCR entry")
    previous_path = target / "metadata.json"
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    if args.version in previous.get("versions", []):
        raise ValueError("Version already published in target registry")
    dest = target / args.version
    shutil.copytree(source / args.version, dest)
    metadata["versions"] = [*previous.get("versions", []), args.version]
    metadata["yanked_versions"] = {
        **previous.get("yanked_versions", {}),
        **metadata.get("yanked_versions", {}),
    }
    previous_path.write_text(json.dumps(metadata, indent=4) + "\n")
    print(dest)


if __name__ == "__main__":
    main()
