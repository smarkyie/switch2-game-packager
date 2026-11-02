# Publishing releases

Downloads are available on the repository's [Releases page](https://github.com/smarkyie/NSP-Box/releases). Each release includes a portable Windows ZIP, portable macOS ZIP and DMG, a source ZIP and SHA-256 checksums.

## Publish a version

1. Commit changes to `main`, update `VERSION` in `src/engine.py`, and add a matching entry in `CHANGELOG.md`.
2. Open **Actions → Build and release app → Run workflow**, select `main`, and run it. Alternatively, push a matching version tag.
3. The workflow runs the synthetic tests on Windows and macOS, builds the portable EXE and the macOS binary and app bundle, and checks PNG/WEBP/ICO/AVIF artwork with NSP in single-file and package-folder modes. It then assembles the application, source, notices and checksums. The Windows job publishes the release and the shared source ZIP first; the macOS job then adds the macOS ZIP, DMG and checksums without overwriting existing assets.
4. A successful job publishes a release tagged at its source commit. Existing releases are not overwritten; use a new version for updated downloads.

Release notes include lawful-use and ownership notices and the current emulator-patch instructions, memory-setting guidance and companion workaround for unpatched builds. Keep these notices and the required dependency licenses with redistributed copies.

## Release contents

`package_release.py` selects application files explicitly. Game dumps, generated game packages, local build reports, game artwork, firmware, retail keys and emulator binaries are excluded. Review the selected files and current compatibility notes before publishing.

Builds run on GitHub's Windows and macOS runners using the workflow's temporary repository token. Generated `build/`, `dist/`, `release/` and `test-work/` directories are ignored by Git. See [BUILD.md](BUILD.md) for local builds.
