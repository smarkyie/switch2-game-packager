# Performance notes — 1.4.0

This release targets large extracted file collections, especially the initial scanning/table stage, and reduces verification I/O. It does not promise a fixed overall speedup.

Version 1.4 adds NSP as a direct streaming target. It does not build an XCI and then convert it; it packages the same content streams straight into PFS0. It adds no input pass and does not create intermediate NCA/XCI files. A synthetic regression test compares source-open counts for XCI and NSP and checks the files written by the NSP path. Full integrity and source-payload verification remain enabled for both.

## Changes

- RomFS sibling linking now takes one pass over the entries. Previously each entry searched its siblings again, which could take quadratic time in a directory with many entries.
- Scanning uses cached directory-entry metadata; constructing file payload parts reuses known sizes.
- Expected source SHA-256 hashes are collected while writing. Verification still independently reads and hashes every output payload, but no longer opens and rereads all the original files.
- Complete NCA digests are reused for CNMT checks. Output hashing uses scoped memoryviews instead of allocating copies of each block.
- File-count feedback distinguishes source scanning from RomFS table creation. JSON reports record stage times.

## Measurements and limits

A Mario Kart World snapshot contained 206,333 source files totaling 23,543,692,736 bytes (206,326 RomFS files). An early 1.3 metadata-only check took 10.30 seconds to inventory the source and 43.91 seconds to construct RomFS tables. These timings were recorded before eliminating the extra per-file stat during payload construction. No game payloads were read in this check. The old version was not timed on this entire snapshot, so no percentage speedup is claimed.

A complete 27-file, 6.62 GB Pokopia snapshot was packaged by 1.2 and 1.3. Both produced exactly the same 6,632,860,672-byte XCI with SHA-256 `a2ff32e3c28477f583421da4ed47d116d684f99f5ebc9567755e53db1928e2f4`. Full output verification passed. Total times were 50.70 and 51.79 seconds respectively; another large packaging job was active on this machine, so this comparison does not establish an overall speedup. The 1.3 report recorded 12.96 seconds in verification. These are development measurements, not a clean-machine benchmark.

Large games still need multiple passes to construct their integrity trees, determine content IDs and write the final image. Hundreds of thousands of tiny files can be slower than a few large files with the same total size. Source/output disk speed, concurrent disk activity and filesystem scanning affect performance. Leave verification enabled for a checked result. An already-running older build continues to use its original code; extract the new release separately and use it for the next job.

Only synthetic fixtures, application source and documentation ship with the app. The real-game test images and source dumps are excluded.
