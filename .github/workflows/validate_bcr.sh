#!/usr/bin/env bash
set -euo pipefail

config=${1:-linux}
registry=$(mktemp -d)
bazel run "--config=$config" //tools/bcr:validate
entry=$(bazel run "--config=$config" //tools/bcr:stage -- --registry="$registry")
consumer="$entry/overlay/examples/smoke"
cd "$consumer"
bazel test "--config=$config" --registry="file://$registry" --registry=https://bcr.bazel.build --lockfile_mode=off //...
bazel build "--config=$config" --registry="file://$registry" --registry=https://bcr.bazel.build --lockfile_mode=off @hermes//:hermesc
