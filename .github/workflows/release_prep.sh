#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail

tag=$1
version=${tag#v}
archive="hermes-${tag}.tar.gz"

# Match GitHub's archive prefix so source and release overrides use the same path.
git archive --format=tar --prefix="hermes-${version}/" "$tag" | gzip -n > "$archive"

cat <<EOF
## Bzlmod

\`\`\`starlark
bazel_dep(name = "hermes", version = "${version}")
\`\`\`

Native Hermes and JSI targets: \`@hermes//:hermes_vm\`, \`@hermes//:headers\`,
\`@hermes//:hermesc\`. Upstream source remains checksum-pinned in \`repositories.bzl\`.
EOF
