"""Generate a BCR entry using upstream sources and native overlay files."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil


def integrity(content: bytes) -> str:
    return "sha256-" + base64.b64encode(hashlib.sha256(content).digest()).decode()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=4) + "\n")


def create_entry(root: Path, registry: Path, version: str) -> Path:
    if not re.fullmatch(r"[0-9][0-9A-Za-z.+-]*", version):
        raise ValueError("Invalid release version")
    proposal = json.loads((root / "release-please-config.json").read_text())
    if version != proposal["packages"]["."]["release-as"]:
        raise ValueError("Version must match release-as")

    pins = (root / "repositories.bzl").read_text()
    commit = re.search(r'^HERMES_COMMIT = "([0-9a-f]{40})"$', pins, re.M)[1]
    checksum = re.search(r'^HERMES_SHA256 = "([0-9a-f]{64})"$', pins, re.M)[1]
    module = (root / "MODULE.bazel").read_text().split("hermes = use_extension(")[0]
    if module.count('version = ""') != 1:
        raise ValueError("Root module version must remain blank")
    module = module.replace('version = ""', f'version = "{version}"').rstrip() + "\n"

    entry = registry / "modules" / "hermes" / version
    # Existing entries must be reviewed explicitly, never silently overwritten.
    entry.mkdir(parents=True)
    overlay = entry / "overlay"
    overlay.mkdir()
    files = {
        "MODULE.bazel": module.encode(),
        "BUILD.bazel": (root / "hermes/hermes.BUILD.bazel").read_bytes(),
        "tests/BUILD.bazel": b'exports_files(["runtime_test.cpp"])\n',
        "tests/runtime_test.cpp": (root / "tests/runtime_test.cpp").read_bytes(),
    }
    for relative in [
        "hermes/configure/BUILD.bazel",
        "hermes/configure/configure.py",
        "examples/smoke/BUILD.bazel",
        "examples/smoke/dist.bzl",
        "examples/smoke/.bazelversion",
    ]:
        files[relative] = (root / relative).read_bytes()
    consumer = (root / "examples/smoke/MODULE.bazel").read_text()
    consumer = re.sub(r"local_path_override\(\n.*?\n\)\n", "", consumer, flags=re.S)
    consumer = consumer.replace('bazel_dep(name = "hermes")', f'bazel_dep(name = "hermes", version = "{version}")')
    files["examples/smoke/MODULE.bazel"] = consumer.encode()
    files["examples/smoke/.bazelrc"] = (root / ".bazelrc").read_bytes()
    for relative, content in files.items():
        dest = overlay / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)

    patches = entry / "patches"
    patches.mkdir()
    patch = "missing_standard_headers.patch"
    shutil.copyfile(root / "hermes" / patch, patches / patch)
    source = {
        "url": f"https://github.com/facebook/hermes/archive/{commit}.tar.gz",
        "integrity": "sha256-" + base64.b64encode(bytes.fromhex(checksum)).decode(),
        "strip_prefix": "hermes-" + commit,
        "overlay": {name: integrity(content) for name, content in sorted(files.items())},
        "patches": {patch: integrity((patches / patch).read_bytes())},
        "patch_strip": 1,
    }
    write_json(entry / "source.json", source)
    (entry / "MODULE.bazel").write_text(module)
    shutil.copyfile(root / ".bcr/presubmit.yml", entry / "presubmit.yml")
    metadata_path = entry.parent / "metadata.json"
    metadata = json.loads((root / ".bcr/metadata.template.json").read_text())
    if metadata_path.exists():
        previous = json.loads(metadata_path.read_text())
        metadata["versions"] = previous["versions"]
        metadata["yanked_versions"] = previous.get("yanked_versions", {})
    if version not in metadata["versions"]:
        metadata["versions"].append(version)
    write_json(metadata_path, metadata)
    return entry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=os.environ.get("BUILD_WORKSPACE_DIRECTORY", "."))
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--version")
    args = parser.parse_args()
    version = args.version or json.loads((args.root / "release-please-config.json").read_text())["packages"]["."]["release-as"]
    print(create_entry(args.root, args.registry, version))


if __name__ == "__main__":
    main()
