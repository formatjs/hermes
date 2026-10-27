"""Materialize a native BCR entry from the maintained overlay."""

import base64
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile


def integrity(content: bytes) -> str:
    return "sha256-" + base64.b64encode(hashlib.sha256(content).digest()).decode()


def versioned_module(content: str, version: str) -> str:
    if content.count('version = ""') != 1:
        raise ValueError("Module template must have one blank version")
    return content.replace('version = ""', f'version = "{version}"')


def generate_entry(root: Path, destination: Path, version: str, commit: str, checksum: str) -> None:
    if not re.fullmatch(r"[0-9][0-9A-Za-z.+-]*", version):
        raise ValueError("Invalid release version")
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or not re.fullmatch(r"[0-9a-f]{64}", checksum):
        raise ValueError("Invalid upstream commit or checksum")
    proposal = json.loads((root / "release-please-config.json").read_text())["packages"]["."]["release-as"]
    if version != proposal:
        raise ValueError("Source pin and release-as must agree")
    source = root / "bcr"
    module = versioned_module((source / "MODULE.bazel").read_text(), version)
    for forbidden in ["use_extension(", "register_toolchains(", "_override("]:
        if forbidden in module:
            raise ValueError(f"Published module contains {forbidden}")
    consumer = versioned_module((source / "overlay/examples/smoke/MODULE.bazel").read_text(), version)
    shutil.copytree(source / "overlay", destination / "overlay")
    shutil.copytree(source / "patches", destination / "patches")
    (destination / "MODULE.bazel").write_text(module)
    (destination / "overlay/MODULE.bazel").write_text(module)
    (destination / "overlay/examples/smoke/MODULE.bazel").write_text(consumer)
    shutil.copyfile(source / "presubmit.yml", destination / "presubmit.yml")
    manifest = {
        "url": f"https://github.com/facebook/hermes/archive/{commit}.tar.gz",
        "integrity": "sha256-" + base64.b64encode(bytes.fromhex(checksum)).decode(),
        "strip_prefix": "hermes-" + commit,
    }
    for kind in ["overlay", "patches"]:
        directory = destination / kind
        manifest[kind] = {
            path.relative_to(directory).as_posix(): integrity(path.read_bytes())
            for path in sorted(directory.rglob("*")) if path.is_file()
        }
    manifest["patch_strip"] = 1
    (destination / "source.json").write_text(json.dumps(manifest, indent=4) + "\n")


def stage_entry(root: Path, registry: Path, version: str, commit: str, checksum: str) -> Path:
    if not re.fullmatch(r"[0-9][0-9A-Za-z.+-]*", version):
        raise ValueError("Invalid release version")
    target = registry / "modules/hermes"
    metadata_path = target / "metadata.json"
    previous = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
    destination = target / version
    if version in previous.get("versions", []) or destination.exists():
        raise ValueError("Version already published in target registry")
    metadata = json.loads((root / "bcr/metadata.json").read_text())
    metadata["versions"] = [*previous.get("versions", []), version]
    metadata["yanked_versions"] = {
        **previous.get("yanked_versions", {}),
        **metadata.get("yanked_versions", {}),
    }
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target) as scratch:
        staged = Path(scratch) / "entry"
        generate_entry(root, staged, version, commit, checksum)
        staged.rename(destination)
    metadata_path.write_text(json.dumps(metadata, indent=4) + "\n")
    return destination
