# Performance notes

## Emulator runtime caution

Considerably lower runtime performance was reported in PokeDinner when using a single package without an external `main.npdm`, even after selecting 12 GiB RAM. This is a user-reported observation, not a controlled FPS benchmark. Keep the companion beside the package for the recommended setup; **Create package folder** is enabled by default. Packaging speed and emulator gameplay performance are separate concerns.

## Packaging efficiency

This release targets large extracted file collections, especially the initial scanning/table stage, and reduces verification I/O. It does not promise a fixed overall speedup.

Version 1.4 adds NSP as a direct streaming target. It does not build an XCI and then convert it; it packages the same content streams straight into PFS0. It adds no input pass and does not create intermediate NCA/XCI files. A synthetic regression test compares source-open counts for XCI and NSP and checks the files written by the NSP path. Full integrity and source-payload verification remain enabled for both.

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
