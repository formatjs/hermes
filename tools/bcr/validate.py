"""Validate committed registry files without changing them."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path


def integrity(content: bytes) -> str:
    return "sha256-" + base64.b64encode(hashlib.sha256(content).digest()).decode()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--checksum", required=True)
    args = parser.parse_args()
    root = Path(os.environ["BUILD_WORKSPACE_DIRECTORY"])
    module = root / "bcr/modules/hermes"
    metadata = json.loads((module / "metadata.json").read_text())
    proposal = json.loads((root / "release-please-config.json").read_text())["packages"]["."]["release-as"]
    if args.version != proposal or args.version not in metadata["versions"]:
        raise ValueError("Source pin, release-as, and checked-in BCR version must agree")
    for version in metadata["versions"]:
        entry = module / version
        source = json.loads((entry / "source.json").read_text())
        registry_module = (entry / "MODULE.bazel").read_bytes()
        if registry_module != (entry / "overlay/MODULE.bazel").read_bytes():
            raise ValueError(f"{version}: registry and overlay MODULE.bazel differ")
        if f'version = "{version}"' not in registry_module.decode():
            raise ValueError(f"{version}: wrong module version")
        for forbidden in [b"use_extension(", b"register_toolchains(", b"_override("]:
            if forbidden in registry_module:
                raise ValueError(f"{version}: published module contains {forbidden.decode()}")
        for kind in ["overlay", "patches"]:
            directory = entry / kind
            files = {path.relative_to(directory).as_posix() for path in directory.rglob("*") if path.is_file()}
            if files != set(source.get(kind, {})):
                raise ValueError(f"{version}: {kind} inventory differs from source.json")
            for name, expected in source.get(kind, {}).items():
                actual = integrity((directory / name).read_bytes())
                if actual != expected:
                    raise ValueError(f"{version}: stale checksum for {kind}/{name}: {actual}")
    source = json.loads((module / args.version / "source.json").read_text())
    expected_integrity = "sha256-" + base64.b64encode(bytes.fromhex(args.checksum)).decode()
    if source["url"] != f"https://github.com/facebook/hermes/archive/{args.commit}.tar.gz" or source["integrity"] != expected_integrity or source["strip_prefix"] != "hermes-" + args.commit:
        raise ValueError("BCR source differs from repositories.bzl pin")
    print("Checked-in BCR overlay valid")


if __name__ == "__main__":
    main()
