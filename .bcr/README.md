# Bazel Central Registry

`bazel run //tools/bcr:entry -- --registry=/path/to/registry --version=VERSION`
generates the registry entry. `source.json` points directly at the pinned
upstream Hermes archive. `overlay/` supplies the module, native build rules,
Python helper, and independent consumer. The header fix remains a patch.

`repositories.bzl` owns the upstream commit/checksum for both publication and
the local development harness. The published module has no source-fetching
extension or development toolchain dependencies.

The consumer module in `examples/smoke` runs on macOS ARM64 and Linux x86_64 with
hermetic LLVM. See [releasing](../docs/releasing.md) for credentials and recovery.
