# CI

BuildBuddy runs two Linux checks on main pushes, merge queue branches, and pull
requests targeting main:

- `Test all targets` checks the public dependency closure with development
  dependencies disabled, then runs the root test suite.
- `Test independent consumer` runs `examples/smoke` tests and builds the exported
  `@hermes//:hermesc` target from that separate module root.

The root suite includes unchanged upstream ADT, Unicode conversion, and regex
tests. The runtime smoke checks JSI evaluation, Promise builtins, and Unicode
property escapes. The consumer repeats that smoke through the public module.

Both roots share `.bazelrc`. `--config=bb-workflow` selects hermetic LLVM 23.1.2
through `llvm` 0.8.25, Linux x86_64 with GNU libc 2.28, and the FormatJS BuildBuddy
service. Remote actions use BuildBuddy's Ubuntu 22.04 image. LLVM remains a
development dependency in each root; consumers choose their own toolchains.
Local builds do not upload remote results by default.

Linux builds both native test suites and macOS ARM64 smoke archives. Only the
target platform changes for macOS; Python helpers and bootstrap `hermesc` stay
on Linux. The LLVM module supplies the macOS SDK.

Enable workflows for `formatjs/hermes` in the FormatJS BuildBuddy organization.
The runner supplies authentication; no API key belongs in this repository.
Untrusted fork builds need an approving review from a trusted collaborator before
RBE can run. A new fork commit needs another approval. GitHub Actions approval is
separate.

GitHub Actions builds the same archives on Linux, then transfers them within
that workflow run. macOS only downloads, checks, and executes those artifacts;
it has no Bazel setup or compilation step. Both the root and independent consumer
archives exercise runtime evaluation and bytecode compilation. BCR presubmit
builds on Linux.
