# Repository guidance

Use Bazel for builds, tests, code generation, and formatting. Keep the overlay
native to `rules_cc`; do not introduce CMake or `rules_foreign_cc`. Never run
`bazel clean` unless explicitly requested.

`repositories.bzl` pins upstream Hermes and its checksum. `bcr/overlay/` owns source
selection, configuration, and code generation; `bcr/patches/` holds source fixes.
Publication generates versioned BCR entries and checksums from these inputs.
Public root targets must load without development dependencies. Consumers select their own toolchains; root
and consumer tests use `hermeticbuild/hermetic-llvm`.

Build Hermes on Linux. Non-Linux workers only run downloaded smoke archives;
do not compile there. After changes, run `bazel run //:format`, then run
`bazel test --config=linux //...` in both roots and
`bazel build --config=linux @hermes//:hermesc` in `examples/smoke`.
Current configurations cover macOS and GNU/Linux on 64-bit ARM/x86; Linux
configuration headers assume glibc. Document validation limits when reporting.

BuildBuddy runs root and independent-consumer checks with `--config=bb-workflow`.
Keep remote execution settings shared by both roots; see [CI](docs/ci.md).
BuildBuddy supplies authentication. Do not commit an API key.

Use Conventional Commits. Follow [docs/releasing.md](docs/releasing.md): keep
`MODULE.bazel` version blank, let Release Please update `version.txt`, and merge
its release PR only after CI passes and its proposed version is approved.
Overlay versions follow the pinned Hermes package version. Snapshots append its
nine-character commit hash; overlay-only revisions append `.bcr.N`.
Update `release-as` when changing the source pin or preparing an overlay revision.
Release tooling uses `//tools/release:release` and its real Release Please
regression test; keep Node.js, npm packages, and JS rules development-only.
Do not invent a published version, push a version tag, or dispatch release/BCR
publication without authorization. Use `formatjs` organization secrets
`GH_RELEASE_TOKEN` and `BCR_PUBLISH_TOKEN`, with an access policy covering this
repository. Never copy credentials from another repository or expand
authentication scopes.
