# Performance notes

## Emulator runtime caution

Without the emulator patch, selecting 12 GiB alone can boot a package with Switch 1 timing and reduced performance; keep the exact external `main.npdm` for that unpatched setup. Version 2.0's corrected emulator patch reads embedded metadata and selects the same 31.25 MHz startup timer as the external-file path in checked PokeDinner/Eglantine builds. A separate companion is not needed after patching and restarting. See [patch instructions and limits](EMULATOR_PATCH.md). This does not guarantee equal FPS in every game or future emulator build.

A user comparison of Mario Kart World NSP versus loose ExeFS/RomFS showed identical settings, 12 GiB memory, executable builds and 31.25 MHz timing. The second (loose-folder) run loaded more cached shader pipelines, so the comparison was affected by cache warm-up. The logs contained no FPS/frame-time measurements and do not establish a format-based performance advantage. Packaging speed and emulator gameplay performance are separate concerns.

## Packaging efficiency

This release targets large extracted file collections, especially the initial scanning/table stage, and reduces verification I/O. It does not promise a fixed overall speedup.

NSP Box streams the same content directly into PFS0 without an intermediate container or temporary NCA files. Verification reuses source SHA-256 values captured while writing, then independently reads back all output integrity trees and payloads. Regression checks bound input reads and reject intermediate container files. Packaging format does not guarantee higher gameplay FPS.

## Changes

- RomFS sibling linking now takes one pass over the entries. Previously each entry searched its siblings again, which could take quadratic time in a directory with many entries.
- Scanning uses cached directory-entry metadata; constructing file payload parts reuses known sizes.
- Expected source SHA-256 hashes are collected while writing. Verification still independently reads and hashes every output payload, but no longer opens and rereads all the original files.
- Complete NCA digests are reused for CNMT checks. Output hashing uses scoped memoryviews instead of allocating copies of each block.
- File-count feedback distinguishes source scanning from RomFS table creation. JSON reports record stage times.

## Measurements and limits

A development dataset with 206,333 files (23.54 GB) took 10.30 seconds to inventory and 43.91 seconds to construct RomFS tables in an early 1.3 build. A separate 27-file dataset produced byte-identical verified output with versions 1.2 and 1.3; total times were 50.70 and 51.79 seconds under concurrent disk activity. These are development measurements, not controlled benchmarks or evidence of an overall speedup.

Large games still need multiple passes to construct their integrity trees, determine content IDs and write the final image. Hundreds of thousands of tiny files can be slower than a few large files with the same total size. Source/output disk speed, concurrent disk activity and filesystem scanning affect performance. Leave verification enabled for a checked result. An already-running older build continues to use its original code; extract the new release separately and use it for the next job.

Only synthetic fixtures, application source and documentation ship with the app. The real-game test images and source dumps are excluded.
