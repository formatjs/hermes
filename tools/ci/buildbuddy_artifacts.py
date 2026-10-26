"""Fetch public smoke archives from successful, matching BuildBuddy workflows."""

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import tarfile
import urllib.parse
import urllib.request

BASE_URL = "https://formatjs.buildbuddy.io"
REPOSITORY = "https://github.com/formatjs/hermes"
ACTIONS = {"root": "Test all targets", "consumer": "Test independent consumer"}
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024


def invocation_id(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "formatjs.buildbuddy.io":
        raise ValueError("Unexpected BuildBuddy invocation host")
    match = re.fullmatch(
        r"/invocation/([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})", parsed.path
    )
    if not match:
        raise ValueError("Invalid BuildBuddy invocation URL")
    return match.group(1)


def artifact_uri(response, expected_sha, workspace):
    action = ACTIONS[workspace]
    invocations = response.get("invocation", [])
    if len(invocations) != 1:
        raise ValueError("Expected one BuildBuddy invocation")
    invocation = invocations[0]
    if (
        invocation.get("commitSha") != expected_sha
        or invocation.get("repoUrl", "").removesuffix(".git") != REPOSITORY
        or invocation.get("pattern") != [action]
        or invocation.get("role") != "CI_RUNNER"
        or invocation.get("readPermission") != "PUBLIC"
        or invocation.get("success") is not True
        or invocation.get("invocationStatus") != "COMPLETE_INVOCATION_STATUS"
    ):
        raise ValueError("Producer does not match the successful public workflow")
    builds = [event.get("buildEvent", {}) for event in invocation.get("event", [])]
    workflows = [build["workflowConfigured"] for build in builds if "workflowConfigured" in build]
    if len(workflows) != 1 or (
        workflows[0].get("actionName") != action
        or workflows[0].get("commitSha") != expected_sha
        or workflows[0].get("targetRepoUrl", "").removesuffix(".git") != REPOSITORY
    ):
        raise ValueError("Unexpected BuildBuddy workflow configuration")
    name = f"hermes-macos-arm64-{workspace}.tar.gz"
    files = [
        file
        for group in invocation.get("targetGroups", [])
        for target in group.get("targets", [])
        for file in target.get("files", [])
    ]
    artifacts = [file for file in files if PurePosixPath(file.get("name", "")).name == name]
    if len(artifacts) != 1:
        raise ValueError("Expected one smoke archive")
    uri = artifacts[0].get("uri", "")
    parsed = urllib.parse.urlsplit(uri)
    if parsed.scheme != "bytestream" or parsed.netloc not in (
        "remote.buildbuddy.io", "formatjs.buildbuddy.io"
    ):
        raise ValueError("Unexpected BuildBuddy artifact URI")
    return uri


def validate_archive(contents):
    with tarfile.open(fileobj=io.BytesIO(contents), mode="r:gz") as archive:
        names = []
        total = 0
        for member in archive:
            name = member.name.removeprefix("./")
            if member.isdir() and name in ("", "."):
                continue
            if not member.isfile() or name not in {"runtime_test", "hermesc"}:
                raise ValueError("Unexpected smoke archive entry")
            if member.mode & 0o777 != 0o755:
                raise ValueError("Smoke binaries must retain executable permissions")
            total += member.size
            if total > MAX_ARCHIVE_BYTES:
                raise ValueError("Smoke archive exceeds extracted size limit")
            names.append(name)
        if sorted(names) != ["hermesc", "runtime_test"]:
            raise ValueError("Smoke archive must contain both binaries exactly once")


def main():
    key = os.environ.get("BUILDBUDDY_API_KEY", "")
    if not key:
        raise ValueError("Organization secret BUILDBUDDY_RO_PUBLIC_KEY is required")
    sha = os.environ["BUILD_SHA"]
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Invalid build commit SHA")
    workspace = os.environ["WORKSPACE_NAME"]
    if workspace not in ACTIONS:
        raise ValueError("Invalid smoke workspace")
    identifier = invocation_id(os.environ["INVOCATION_URL"])
    request = urllib.request.Request(
        BASE_URL + "/rpc/BuildBuddyService/GetInvocation",
        data=json.dumps({"lookup": {"invocationId": identifier}}).encode(),
        headers={"Content-Type": "application/json", "x-buildbuddy-api-key": key},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        uri = artifact_uri(json.load(response), sha, workspace)
    query = urllib.parse.urlencode({
        "invocation_id": identifier,
        "bytestream_url": uri,
        "filename": "smoke.tar.gz",
    })
    request = urllib.request.Request(
        BASE_URL + "/file/download?" + query,
        headers={"x-buildbuddy-api-key": key},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        contents = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(contents) > MAX_ARCHIVE_BYTES:
        raise ValueError("Smoke archive exceeds download size limit")
    validate_archive(contents)
    destination = Path("artifacts")
    destination.mkdir(exist_ok=False)
    (destination / "smoke.tar.gz").write_bytes(contents)
    (destination / "smoke.tar.gz.sha256").write_text(
        hashlib.sha256(contents).hexdigest() + "  smoke.tar.gz\n"
    )
    print(f"Downloaded {workspace} smoke archive for {sha} from {identifier}")


if __name__ == "__main__":
    main()
