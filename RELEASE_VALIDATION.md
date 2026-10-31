# Release validation

## Version 1.4.1

- All 36 synthetic tests passed locally on Windows x64: the original packaging/UI/artwork cases plus NACP offsets and compressed-title preservation, exact NPDM companions for both formats, conflicting/concurrently created companion preservation, cancellation cleanup, and explicit compatibility setup without overwriting existing keys.
- In a separate PokeDinner 2.0.0 profile (binary reports commit 70ecb39ef0), a Pokopia NSP exited and an MK World XCI hit an early memory fault without a companion. The extracted MK World snapshot rendered in that same profile. With the exact snapshot NPDM beside each package and the local plaintext compatibility entries present, Pokopia NSP rendered its language screen and MK World XCI rendered. Logs confirmed the Switch 2 12 GiB layout and 31.25 MHz clock. This is a launch/rendering check, not exhaustive gameplay validation or an FPS benchmark.
- The GitHub release workflow requires the full synthetic suite, a portable Windows build, and eight frozen-EXE packaging checks (PNG/WEBP/ICO/AVIF in both output formats) before it can publish. Those checks also require the exact companion beside each output.
- No real game files, companions, artwork, emulator binaries, private logs or retail keys are included in the repository/release. Compatibility placeholders are generated locally and cannot decrypt retail content.

## Earlier version 1.4.0 validation

Validation performed on Windows x64 on 2026-10-31.

- Seven synthetic tests passed: Unicode/multiple-version round trip with a different title ID; exact embedded artwork and generated title/version; preservation of existing output; cancellation cleanup; invalid NPDM; empty RomFS; refusal to save inside RomFS; artwork fit/alpha handling. Some checks are grouped within individual test cases.
- The optimized engine was tested with a complete 27-file Pokémon Pokopia snapshot. Versions 1.2 and 1.3 produced a byte-identical 6,632,860,672-byte XCI, with full verification passing. Measurements and concurrent-load limitations are recorded in PERFORMANCE_NOTES.md. The final cached-file-size change was then checked with the synthetic suites. No game files or artwork are included in this distribution.
- Three UI integration tests passed (including crop apply/cancel state and mocked clipboard image/file handling): native Windows shell drops of a folder and artwork, snapshot selection, metadata editing, artwork removal, a verified build through the UI, control enable/disable behavior, notes access, time-based animation interpolation, reduced-motion behavior, and visibility of controls at the minimum window size.
- Four artwork tests passed, covering crop positioning, non-destructive input handling, fit mode, invalid bounds, and WEBP/GIF/TIFF/BMP/ICO/ICNS/AVIF/JPEG2000 decoding.
- Four performance-safety tests passed: no redundant source opens during readback, corrupted output rejection, changed input rejection and release of mmap views after failed IVFC validation.
- Six NSP tests passed: full payload/metadata/artwork and standalone-verifier round trip; no extra source opens or intermediate XCI; cancellation cleanup; corruption detection; no-overwrite/format mismatch; CLI format inference/explicit selection. An additional UI test builds NSP through the format selector and verifies path/button/completion updates and busy-state locking. All 25 synthetic tests passed.
- The artwork editor and redesigned GUI were visually inspected. Icons and rounded surfaces are supersampled for antialiasing. There is no animations toggle. Windows reduced-motion preferences are respected.
- The final frozen EXE was smoke-tested eight times: synthetic PNG, WEBP, ICO and AVIF artwork in both XCI and NSP, producing verified packages and version 1.4.0 reports. Full gameplay/rendering and a real-game NSP launch are not part of this release validation.
- Eglantine previously accepted the same container construction and loaded the game's executable modules. Emulator gameplay/rendering is not part of this app's release validation. No claim is made that every game or emulator fork has been tested.
- The release is curated from the application source, runtime EXE, notices and documentation. Local dumps, test XCIs, reports containing private paths, downloaded product artwork, and emulator binaries are excluded.

The test source is included so other people can repeat the synthetic checks without game content. A clean Windows VM without Python was not available; portability was checked by running the frozen EXE with its bundled runtime on the development Windows installation.
