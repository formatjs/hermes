"""Validate release inputs by generating a temporary registry entry."""

import argparse
import os
from pathlib import Path
import tempfile

from tools.bcr.entry import stage_entry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--checksum", required=True)
    args = parser.parse_args()
    root = Path(os.environ["BUILD_WORKSPACE_DIRECTORY"])
    with tempfile.TemporaryDirectory() as registry:
        stage_entry(root, Path(registry), args.version, args.commit, args.checksum)
    print("BCR overlay inputs valid")


if __name__ == "__main__":
    main()
