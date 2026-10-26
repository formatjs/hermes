"""Check the published module has no dependency on the development wrapper."""

import json
from pathlib import Path
import tempfile
import unittest

from tools.bcr.entry import create_entry, integrity


class EntryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "root"
        self.registry = Path(self.temp.name) / "registry"
        self.version = "1.0.0-123456789"
        files = {
            "release-please-config.json": json.dumps({"packages": {".": {"release-as": self.version}}}),
            "repositories.bzl": 'HERMES_COMMIT = "' + "1" * 40 + '"\nHERMES_SHA256 = "' + "2" * 64 + '"\n',
            "MODULE.bazel": 'module(name = "hermes", version = "")\nbazel_dep(name = "rules_cc", version = "0.2.27")\nhermes = use_extension("//:repositories.bzl", "hermes")\nbazel_dep(name = "llvm", dev_dependency = True)\n',
            "hermes/hermes.BUILD.bazel": 'cc_library(name = "hermes_vm")\n',
            "hermes/missing_standard_headers.patch": "header patch\n",
            "tests/runtime_test.cpp": "int main() {}\n",
            ".bcr/metadata.template.json": '{"versions": [], "yanked_versions": {}}',
            ".bcr/presubmit.yml": "bcr_test_module: {}\n",
            "examples/smoke/MODULE.bazel": 'bazel_dep(name = "hermes")\nlocal_path_override(\n    module_name = "hermes",\n    path = "../..",\n)\nbazel_dep(name = "llvm", dev_dependency = True)\n',
            "examples/smoke/BUILD.bazel": "# consumer\n",
            "examples/smoke/dist.bzl": "# transition\n",
            "examples/smoke/.bazelversion": "9.3.0\n",
            ".bazelrc": "build:linux --compilation_mode=opt\n",
            "hermes/configure/BUILD.bazel": "# Python helper\n",
            "hermes/configure/configure.py": "# configure\n",
        }
        for relative, content in files.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    def test_published_module_is_self_contained(self):
        entry = create_entry(self.root, self.registry, self.version)
        source = json.loads((entry / "source.json").read_text())
        self.assertIn("github.com/facebook/hermes/archive/", source["url"])
        module = (entry / "MODULE.bazel").read_text()
        self.assertEqual(module, (entry / "overlay/MODULE.bazel").read_text())
        self.assertNotIn("use_extension", module)
        self.assertNotIn('name = "llvm"', module)
        self.assertIn(self.version, module)
        for relative, digest in source["overlay"].items():
            self.assertEqual(digest, integrity((entry / "overlay" / relative).read_bytes()))
        consumer = (entry / "overlay/examples/smoke/MODULE.bazel").read_text()
        self.assertNotIn("local_path_override", consumer)
        self.assertIn(self.version, consumer)
        self.assertIn('name = "llvm"', consumer)

    def test_existing_entry_is_not_overwritten(self):
        entry = create_entry(self.root, self.registry, self.version)
        with self.assertRaises(FileExistsError):
            create_entry(self.root, self.registry, self.version)
        self.assertTrue((entry / "source.json").exists())

    def test_wrong_version_rejected(self):
        with self.assertRaises(ValueError):
            create_entry(self.root, self.registry, "2.0.0")


if __name__ == "__main__":
    unittest.main()
