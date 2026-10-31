# GitHub releases

The canonical source is the private repository `smarkyie/switch2-game-packager`. Downloads are under its **Releases** page; only the owner and invited collaborators can access them. This repository does not grant access to any other repository or account data.

## Publish the next version

1. Commit the application changes to `main`, update `VERSION` in `src/engine.py`, and add a matching section in `CHANGELOG.md`.
2. Open **Actions → Build and release Windows app → Run workflow**, choose `main`, and run it. Alternatively, push a matching version tag such as `v1.4.1`.
3. GitHub runs all synthetic tests on Windows, builds the portable EXE, smoke-tests PNG/WEBP/ICO/AVIF artwork with both XCI and NSP, and assembles allowlisted source/portable ZIPs plus checksums.
4. The job creates a release with a tag pointing to the source commit. Existing releases are not overwritten. Confirm the job is green before sharing the private release link.

Builds run on GitHub's Windows runner. No personal access token or persistent new credential is required: the job uses its short-lived repository token. Workflow write access is restricted to repository contents for publishing its own release. Private repositories use the account's GitHub Actions allowance; this project does not change billing or spending settings.

## Local storage

Keep one small source checkout for editing. Release downloads live on GitHub; there is no need to retain separate local copies for every version. Building locally remains possible with `BUILD.md`, and generated `build/`, `dist/`, `release/` and `test-work/` folders are ignored by Git.

Game dumps, generated XCI/NSP/NCA files, reports containing local paths, retail keys, firmware and downloaded game artwork are excluded. The release script explicitly selects application files rather than archiving the whole workspace. Generated compatibility entries are local placeholders and cannot decrypt retail content.
