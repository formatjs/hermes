# Bazel Central Registry

`modules/hermes/<version>/` is the complete registry entry. `source.json` points
at upstream Hermes; `overlay/` contains the reviewed Bazel files. Local builds
use these same build definitions, configuration rule, and header patch.

Run `bazel run //tools/bcr:validate` after edits. It checks source pins, versions,
file inventories, and checksums without rewriting files. Update stale hashes
in `source.json` before committing.

Publication copies the selected entry with `//tools/bcr:stage`, preserves the
registry's other versions, adds provenance attestations, and opens the BCR PR.
No overlay files are generated during release.
