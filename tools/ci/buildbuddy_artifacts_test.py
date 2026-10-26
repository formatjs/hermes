"""Check the producer and archive boundaries before executing smoke binaries."""

import copy
import io
import tarfile
import unittest

from tools.ci import buildbuddy_artifacts as artifacts

SHA = "a" * 40
URI = "bytestream://remote.buildbuddy.io/blobs/" + "b" * 64 + "/100"


def producer():
    return {"invocation": [{
        "commitSha": SHA,
        "repoUrl": artifacts.REPOSITORY,
        "pattern": [artifacts.ACTIONS["root"]],
        "role": "CI_RUNNER",
        "readPermission": "PUBLIC",
        "success": True,
        "invocationStatus": "COMPLETE_INVOCATION_STATUS",
        "event": [{"buildEvent": {"workflowConfigured": {
            "actionName": artifacts.ACTIONS["root"],
            "commitSha": SHA,
            "targetRepoUrl": artifacts.REPOSITORY + ".git",
        }}}],
        "targetGroups": [{"targets": [{"files": [{
            "name": "command-3/hermes-macos-arm64-root.tar.gz", "uri": URI,
        }]}]}],
    }]}


def archive(entries):
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as output:
        for name, kind in entries:
            member = tarfile.TarInfo(name)
            member.mode = 0o755
            member.type = kind
            if kind == tarfile.SYMTYPE:
                member.linkname = "/tmp/other"
                output.addfile(member)
            else:
                member.size = 1
                output.addfile(member, io.BytesIO(b"x"))
    return data.getvalue()


class ArtifactTest(unittest.TestCase):
    def test_matching_public_workflow(self):
        self.assertEqual(artifacts.artifact_uri(producer(), SHA, "root"), URI)

    def test_rejects_other_producers(self):
        for field, value in {
            "commitSha": "c" * 40,
            "repoUrl": "https://github.com/other/hermes",
            "pattern": [artifacts.ACTIONS["consumer"]],
            "role": "BB_WORKFLOW",
            "readPermission": "GROUP",
            "success": False,
            "invocationStatus": "PARTIAL_INVOCATION_STATUS",
        }.items():
            with self.subTest(field=field), self.assertRaises(ValueError):
                response = producer()
                response["invocation"][0][field] = value
                artifacts.artifact_uri(response, SHA, "root")

    def test_rejects_wrong_workflow_repository(self):
        response = producer()
        workflow = response["invocation"][0]["event"][0]["buildEvent"]["workflowConfigured"]
        workflow["targetRepoUrl"] = "https://github.com/other/hermes"
        with self.assertRaises(ValueError):
            artifacts.artifact_uri(response, SHA, "root")

    def test_rejects_ambiguous_archive(self):
        response = producer()
        files = response["invocation"][0]["targetGroups"][0]["targets"][0]["files"]
        files.append(copy.deepcopy(files[0]))
        with self.assertRaises(ValueError):
            artifacts.artifact_uri(response, SHA, "root")

    def test_rejects_external_artifact_uri(self):
        response = producer()
        response["invocation"][0]["targetGroups"][0]["targets"][0]["files"][0]["uri"] = "https://example.com/code"
        with self.assertRaises(ValueError):
            artifacts.artifact_uri(response, SHA, "root")

    def test_invocation_url(self):
        identifier = "12345678-1234-1234-1234-123456789abc"
        self.assertEqual(artifacts.invocation_id(artifacts.BASE_URL + "/invocation/" + identifier), identifier)
        for url in ("http://formatjs.buildbuddy.io/invocation/" + identifier,
                    "https://other.example/invocation/" + identifier,
                    artifacts.BASE_URL + "/invocation/not-an-id"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                artifacts.invocation_id(url)

    def test_archive_has_exact_executable_payload(self):
        artifacts.validate_archive(archive([
            ("runtime_test", tarfile.REGTYPE), ("hermesc", tarfile.REGTYPE),
        ]))

    def test_rejects_archive_substitution(self):
        for entries in (
            [("../runtime_test", tarfile.REGTYPE), ("hermesc", tarfile.REGTYPE)],
            [("runtime_test", tarfile.SYMTYPE), ("hermesc", tarfile.REGTYPE)],
            [("runtime_test", tarfile.REGTYPE)],
            [("runtime_test", tarfile.REGTYPE), ("runtime_test", tarfile.REGTYPE), ("hermesc", tarfile.REGTYPE)],
        ):
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                artifacts.validate_archive(archive(entries))


if __name__ == "__main__":
    unittest.main()
