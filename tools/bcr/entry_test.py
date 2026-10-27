"""Exercise immutable publication snapshots from maintained overlay inputs."""

import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.bcr.entry import stage_entry


VERSION = "1.2.3.bcr.1"
COMMIT = "a" * 40
CHECKSUM = "ab" * 32

def files_under(directory: Path) -> dict[str, bytes]:
    return {path.relative_to(directory).as_posix(): path.read_bytes()
            for path in directory.rglob("*") if path.is_file()}


class EntryTest(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name) / "source"
        self.registry = Path(self.scratch.name) / "registry"
        self.root.mkdir()
        inputs = {
            "release-please-config.json": json.dumps({"packages": {".": {"release-as": VERSION}}}),
            "bcr/MODULE.bazel": 'module(name = "hermes", version = "")\n',
            "bcr/overlay/BUILD.bazel": 'exports_files(["payload.bin"])\n',
            "bcr/overlay/payload.bin": "upstream build metadata",
            "bcr/overlay/examples/smoke/MODULE.bazel": 'bazel_dep(name = "hermes", version = "")\n',
            "bcr/patches/01-fix.patch": "source fix\n",
            "bcr/metadata.json": json.dumps({"maintainers": [{"github": "maintainer"}]}),
            "bcr/presubmit.yml": "bcr_test_module:\n  module_path: examples/smoke\n",
        }
        for name, content in inputs.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    def stage(self, version=None):
        return stage_entry(self.root, self.registry, version or VERSION, COMMIT, CHECKSUM)

    def test_generated_entry_is_complete_and_reproducible(self):
        before = files_under(self.root)
        entry = self.stage()
        self.assertEqual(files_under(self.root), before)
        module = (entry / "MODULE.bazel").read_bytes()
        self.assertIn(f'version = "{VERSION}"'.encode(), module)
        self.assertEqual(module, (entry / "overlay/MODULE.bazel").read_bytes())
        self.assertIn(f'version = "{VERSION}"', (entry / "overlay/examples/smoke/MODULE.bazel").read_text())
        source = json.loads((entry / "source.json").read_text())
        self.assertEqual(source["url"], f"https://github.com/facebook/hermes/archive/{COMMIT}.tar.gz")
        self.assertEqual(source["strip_prefix"], "hermes-" + COMMIT)
        self.assertEqual(source["integrity"], "sha256-" + base64.b64encode(bytes.fromhex(CHECKSUM)).decode())
        for kind in ["overlay", "patches"]:
            payload = files_under(entry / kind)
            self.assertEqual(set(source[kind]), set(payload))
            for name, content in payload.items():
                expected = "sha256-" + base64.b64encode(hashlib.sha256(content).digest()).decode()
                self.assertEqual(source[kind][name], expected, name)
        self.assertEqual(source["patch_strip"], 1)
        self.assertEqual((entry / "presubmit.yml").read_bytes(), before["bcr/presubmit.yml"])
        second = stage_entry(self.root, Path(self.scratch.name) / "second", VERSION, COMMIT, CHECKSUM)
        self.assertEqual(files_under(entry), files_under(second))

    def test_next_release_preserves_existing_entry_and_yanks(self):
        previous = self.stage()
        snapshot = files_under(previous)
        metadata_path = previous.parent / "metadata.json"
        metadata = json.loads(metadata_path.read_text())
        metadata["yanked_versions"] = {VERSION: "retired by registry maintainer"}
        metadata_path.write_text(json.dumps(metadata))
        config_path = self.root / "release-please-config.json"
        config = json.loads(config_path.read_text())
        next_version = VERSION + ".next"
        config["packages"]["."]["release-as"] = next_version
        config_path.write_text(json.dumps(config))
        build = self.root / "bcr/overlay/BUILD.bazel"
        build.write_text(build.read_text() + "\n# Updated overlay\n")
        current = self.stage(next_version)
        self.assertEqual(files_under(previous), snapshot)
        self.assertEqual((current / "overlay/BUILD.bazel").read_bytes(), build.read_bytes())
        self.assertNotEqual(json.loads((current / "source.json").read_text())["overlay"]["BUILD.bazel"],
                            json.loads(snapshot["source.json"])["overlay"]["BUILD.bazel"])
        metadata = json.loads(metadata_path.read_text())
        self.assertEqual(metadata["versions"], [VERSION, next_version])
        self.assertEqual(metadata["yanked_versions"], {VERSION: "retired by registry maintainer"})

    def test_existing_version_cannot_be_overwritten(self):
        entry = self.stage()
        before = files_under(self.registry)
        with self.assertRaisesRegex(ValueError, "already published"):
            self.stage()
        self.assertEqual(files_under(self.registry), before)
        (entry.parent / "metadata.json").unlink()
        before = files_under(self.registry)
        with self.assertRaisesRegex(ValueError, "already published"):
            self.stage()
        self.assertEqual(files_under(self.registry), before)

    def test_invalid_proposal_cannot_publish(self):
        for version in ["../escape", VERSION + ".wrong"]:
            with self.subTest(version=version), self.assertRaises(ValueError):
                self.stage(version)
        self.assertEqual(files_under(self.registry), {})
        module = self.root / "bcr/MODULE.bazel"
        module.write_text(module.read_text() + '\nuse_extension("//:private.bzl", "private")\n')
        with self.assertRaisesRegex(ValueError, "Published module"):
            self.stage()
        self.assertEqual(files_under(self.registry), {})


if __name__ == "__main__":
    unittest.main()
