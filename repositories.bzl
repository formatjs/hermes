"""Pinned upstream Hermes sources for the native Bazel overlay."""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

HERMES_COMMIT = "393a539e645944a6ce879afc18ea8ddaa9232a08"
HERMES_SHA256 = "5fce2dbb3b9046b21b717de30d9e5192f756420e12daf967dddee3a32d975a51"

def _hermes_impl(module_ctx):
    http_archive(
        name = "hermes_src",
        build_file = Label("//hermes:hermes.BUILD.bazel"),
        patches = [Label("//hermes:missing_standard_headers.patch")],
        patch_args = ["-p1"],
        sha256 = HERMES_SHA256,
        strip_prefix = "hermes-" + HERMES_COMMIT,
        urls = ["https://github.com/facebook/hermes/archive/" + HERMES_COMMIT + ".tar.gz"],
    )
    return module_ctx.extension_metadata(
        root_module_direct_deps = ["hermes_src"],
        root_module_direct_dev_deps = [],
        reproducible = True,
    )

hermes = module_extension(implementation = _hermes_impl)
