# Source provenance

`repositories.bzl` downloads upstream Hermes at commit
`393a539e645944a6ce879afc18ea8ddaa9232a08`, checked against SHA-256
`5fce2dbb3b9046b21b717de30d9e5192f756420e12daf967dddee3a32d975a51`.
The downloaded tree retains its Meta MIT license and third-party notices.
`missing_standard_headers.patch` adds standard includes required by LLVM 23's
libc++ headers.

The overlay is authored directly from that Hermes revision's target and source
declarations. Source lists follow `lib/CMakeLists.txt` and its subdirectories,
`external/llvh/lib`, `API/hermes`, `API/jsi/jsi`, and `public/hermes/Public`.
These files supply build metadata only; Bazel runs native `rules_cc` actions.
Configuration headers, typed-library includes, and internal bytecode are generated
from the pinned sources, with a compiler built for the execution platform.

The overlay itself uses the root MIT license. LLVM and Python toolchains retain
their upstream licenses and are fetched through their Bazel modules.
