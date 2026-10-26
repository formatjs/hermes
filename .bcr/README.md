# Bazel Central Registry

Release workflows publish this overlay through
[publish-to-bcr](https://github.com/bazel-contrib/publish-to-bcr). Templates point
at the overlay release archive; `repositories.bzl` separately pins upstream
Hermes source and its checksum.

The consumer module in `examples/smoke` runs on macOS ARM64 and Linux x86_64 with
hermetic LLVM. See [releasing](../docs/releasing.md) for credentials and recovery.
