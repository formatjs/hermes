# Hermes for Bazel

Native Bazel overlay for [facebook/hermes](https://github.com/facebook/hermes),
pinned to static_h commit
[`393a539e645944a6ce879afc18ea8ddaa9232a08`](https://github.com/facebook/hermes/commit/393a539e645944a6ce879afc18ea8ddaa9232a08).
Uses `rules_cc`, Bazel template actions, hermetic code generation, and
[hermeticbuild/hermetic-llvm](https://github.com/hermeticbuild/hermetic-llvm).

## Consume

Until the first BCR entry lands, use a commit-pinned
`archive_override` for this repository, or `local_path_override` for a checkout:

```starlark
bazel_dep(name = "hermes")
local_path_override(module_name = "hermes", path = "/path/to/hermes")

bazel_dep(name = "llvm", version = "0.8.25", dev_dependency = True)
register_toolchains("@llvm//toolchain:all", dev_dependency = True)
```

BCR downloads upstream Hermes directly and applies the registry's `overlay/`
build files. The checkout override above uses a development harness that fetches
the same pinned source. Consumers use:

- `@hermes//:hermes_vm`: Hermes runtime, compiler support, and JSI.
- `@hermes//:headers`: public Hermes and JSI headers.
- `@hermes//:hermesc`: bytecode compiler; code generation builds it for execution.

Consumers select their C/C++ toolchain. This repository's tests use hermetic LLVM
23.1.2 through module `llvm` 0.8.25. Byte embedding uses Bazel's Python toolchain.

`rules_cc`, `rules_python`, `platforms`, and `package_metadata` remain normal
dependencies: consumers load them while building Hermes. LLVM, formatting, and
root Python version selection are development dependencies.

## Build

Run builds on Linux:

```sh
bazel test --config=linux //...
cd examples/smoke
bazel test --config=linux //...
bazel build --config=linux @hermes//:hermesc
```

The consumer test evaluates JavaScript through JSI, including Unicode regexp
properties and Promise builtins loaded from generated internal bytecode.
Root tests also run upstream ADT, Unicode conversion, and regex suites.
CI covers macOS ARM64 and Linux x86_64 with GNU libc; BCR presubmit builds on
Linux. Linux configuration assumes glibc; hermetic LLVM's
default GNU target uses glibc 2.28. Musl is outside the current header setup.
Other target configurations have not been validated.

BuildBuddy runs Linux checks and cross-compiles macOS smoke archives through
`with_cfg`. GitHub Actions only downloads and runs them. See [CI](docs/ci.md).

The runtime uses Hades GC and Unicode Lite, with built-in Intl and debugger
disabled. Embedders can install native Intl implementations through JSI.

## Upkeep

`repositories.bzl` owns the source commit/checksum and selected BCR version.
The `.bcr.1` revision fixes proxy construction: construct traps do not read
`newTarget.prototype`; forwarded constructors allocate their own receiver.
Runtime smoke tests cover trap order, derived constructors, and nested proxies.
`bcr/modules/hermes/<version>/overlay/` holds the build definitions and helpers.
Updating Hermes requires reviewing source lists, configuration headers, and
internal-bytecode generation,
then running root and consumer tests. `bazel run //:format` formats Bazel files.

Release automation follows
[rules_formatjs](https://github.com/formatjs/rules_formatjs). See
[releasing](docs/releasing.md) and [source provenance](docs/provenance.md).
