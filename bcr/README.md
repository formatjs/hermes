# Bazel Central Registry

Maintain `overlay/`, `patches/`, `MODULE.bazel`, `presubmit.yml`, and
`metadata.json` here. Both module templates keep their version blank.
`repositories.bzl` pins upstream Hermes, its checksum, and the proposed version;
local builds use these same overlay files and patches.

`bazel run //tools/bcr:validate` checks the release proposal and generates a
temporary entry. CI builds that generated entry as an independent consumer.

`bazel run //tools/bcr:stage -- --registry=/path/to/registry` materializes
`modules/hermes/<version>/`: stamps both module templates, copies overlay files
and patches, and computes `source.json` inventories and checksums. Patches apply
in filename order. Publication attests this entry and opens the BCR PR.
Existing registry versions and yank records stay intact; publishing over an
existing version fails. Historical snapshots live in BCR and release tags.

For a version bump, edit the source pin/checksum and proposed version in
`repositories.bzl`, then match `release-as`. Review upstream compatibility and
run root, consumer, and generated-entry checks. No version directories or
checksums need hand editing.
