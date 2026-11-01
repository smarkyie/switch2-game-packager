# NSP Box technical notes

NSP Box packages a complete, already-extracted game snapshot or a separate DLC RomFS. It does not decrypt content, merge delta updates, create retail signatures or emit XCI files. The Game and DLC tabs stream directly into NSP/PFS0.

## Container and integrity

Game packages contain unsigned plaintext Program, Control and Meta NCAs. Program ExeFS uses PFS0 with hierarchical SHA-256; RomFS uses binary directory/file tables and an IVFC integrity tree. Selected artwork is encoded as a cropped 256×256 JPEG in Control RomFS. Existing control metadata is retained when present; generated metadata is minimal.

Meta PFS0 contains an Application CNMT linking content IDs, sizes and SHA-256 hashes. DLC contains a Data NCA and AddOnContent CNMT/Meta NCA, with no executable or external companion. See [DLC.md](DLC.md) for the mapping, generated metadata and limitations.

Source files are streamed through a Blob/FilePart representation. The writer checks file sizes/short reads, cancellation and final modification timestamps. Verification uses SHA-256 captured during the final write to avoid another source-read pass, while independently checking all container metadata, integrity-tree levels and packed file contents. Unfinished output is removed. Existing destinations are refused.

Both paths support packages up to 32 GiB. NSP is uncompressed; output size broadly follows input size. Packaging performance and emulator gameplay speed are separate concerns.

## Native Windows drops — issue #2

The original Windows procedure called root.after directly while handling WM_DROPFILES. Posting a native image drop during real Tk mainloop reproduced a fatal PyEval_RestoreThread error. Calling update() in the older UI tests did not expose this failure.

The fixed procedure only queries the HDROP paths, queues Python values and releases the handle with DragFinish. It does not invoke Tcl/Tk. A pre-scheduled Tk timer drains the queue and calls the application's normal drop handler. Shutdown cancels the timer before restoring the original window procedure. Tests exercise real mainloop with repeated PNG/WEBP/folder drops and Unicode paths; the frozen EXE is also checked using native drop messages addressed only to its own child process.

References: [CPython _tkinter](https://github.com/python/cpython/blob/v3.11.9/Modules/_tkinter.c), [Tkinter threading model](https://docs.python.org/3/library/tkinter.html#threading-model), [WM_DROPFILES](https://learn.microsoft.com/en-us/windows/win32/shell/wm-dropfiles), [reported issue](https://github.com/smarkyie/switch2-game-packager/issues/2).

## Emulator compatibility and privacy

The optional reversible emulator patch reads embedded metadata before Switch 2 mode selection. Keep its original backup/state directory until removal; identifiers and old payloads remain compatible with existing installations. The patch is experimental and cannot add emulation services that a fork lacks. See [EMULATOR_PATCH.md](EMULATOR_PATCH.md).

Placeholder key labels retain their historical fixed values for compatibility. They are locally generated values, not Nintendo keys, and cannot decrypt retail games. Setup runs only on explicit selection and does not replace prod.keys.

No game/DLC files, artwork, firmware or emulator binaries are included in app/source downloads. No telemetry or automatic upload is implemented. Review locally generated reports before sharing them because they contain input/output paths. See [DISCLAIMER.md](DISCLAIMER.md), [BUILD.md](BUILD.md) and [RELEASE_VALIDATION.md](RELEASE_VALIDATION.md).
