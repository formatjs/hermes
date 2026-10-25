# Source provenance

`repositories.bzl` downloads upstream Hermes at commit
`393a539e645944a6ce879afc18ea8ddaa9232a08`, checked against SHA-256
`5fce2dbb3b9046b21b717de30d9e5192f756420e12daf967dddee3a32d975a51`.
The downloaded tree retains its Meta MIT license and third-party notices.

The native build layout was informed by
[Snapchat/Valdi's Hermes overlay](https://github.com/Snapchat/Valdi/blob/ede1462368bbc233c507dd7136a3602d457a56b8/third-party/hermes/hermes.BUILD).
Its MIT notice is retained in [Valdi.txt](../LICENSES/Valdi.txt).
Configuration and internal bytecode are generated for the pinned source;
Valdi's older prepared headers and bytecode are not imported.

The overlay itself uses the root MIT license. LLVM and Python toolchains retain
their upstream licenses and are fetched through their Bazel modules.
