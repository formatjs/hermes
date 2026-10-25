# Repository guidance

Use Bazel for builds, tests, code generation, and formatting. Keep the overlay
native to `rules_cc`; do not introduce CMake or `rules_foreign_cc`. Never run
`bazel clean` unless explicitly requested.

`repositories.bzl` pins upstream Hermes and its checksum. `hermes/` owns source
selection, configuration, and code generation. Public root targets must load
without development dependencies. Consumers select their own toolchains; root
and consumer tests use `hermeticbuild/hermetic-llvm`.

After changes, run `bazel run //:format` and `bazel test //...`, then run
`bazel test //...` and `bazel build @hermes//:hermesc` in `examples/smoke`.
Current configurations cover macOS and GNU/Linux on 64-bit ARM/x86; Linux
configuration headers assume glibc. Document validation limits when reporting.

Use Conventional Commits. Follow [docs/releasing.md](docs/releasing.md): keep
`MODULE.bazel` version blank, let Release Please update `version.txt`, and merge
its release PR only after CI passes and its proposed version is approved.
Do not invent a published version, push a version tag, or dispatch release/BCR
publication without authorization. Repository secrets are maintainer setup;
never copy credentials from another repository or expand authentication scopes.
