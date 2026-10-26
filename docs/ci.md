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

BuildBuddy builds both Linux test suites and macOS ARM64 smoke archives.
`with_cfg` targets transition archive dependencies to macOS and opt mode; Python
helpers and bootstrap `hermesc` stay on Linux. The LLVM module supplies the SDK.

Enable workflows for `formatjs/hermes` in the FormatJS BuildBuddy organization.
The runner supplies authentication; no API key belongs in this repository.
Artifact downloads use the organization secret `BUILDBUDDY_RO_PUBLIC_KEY`, with
Hermes included in its repository access policy. It needs read-only access to
the FormatJS BuildBuddy cache; public invocation metadata alone cannot read it.
Untrusted fork builds need an approving review from a trusted collaborator before
RBE can run. A new fork commit needs another approval. GitHub Actions approval is
separate.

GitHub Actions reacts to successful BuildBuddy statuses, verifies the producer's
repository, commit, action, and archive, then transfers it to macOS. It does not
repeat the build or Linux tests. macOS only checks and executes those artifacts;
it has no Bazel setup or compilation step. Both archives exercise runtime
evaluation and bytecode compilation. BCR presubmit builds on Linux.
