"""Generate a versioned Hermes entry in a registry checkout."""

import argparse
import os
from pathlib import Path

from tools.bcr.entry import stage_entry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--checksum", required=True)
    args = parser.parse_args()
    root = Path(os.environ["BUILD_WORKSPACE_DIRECTORY"])
    print(stage_entry(root, args.registry, args.version, args.commit, args.checksum))


if __name__ == "__main__":
    main()
