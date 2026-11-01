# Validation and compatibility

## Automated checks

### 2.0 release checks

All 51 unit/UI/native tests and all 16 frozen Windows XCI/NSP packaging checks passed for 2.0.0. The Windows 2.0 release includes the corrected 1.5.1 native probe. No Linux build is included. User-provided Mario Kart World logs from NSP and loose-folder runs both select 12 GiB, the 31.25 MHz timer and identical settings/module builds. The second run had a warmer shader cache; no FPS/frame-time data was logged, so no format performance advantage is claimed. The user reported the corrected patch working.

### Local 1.5.1 correction

All 51 unit/UI/native tests and 16 frozen Windows packaging cases passed for
1.5.1. The 1.5.0 simulated VFS callbacks modeled PokeDinner's Read method incorrectly.
Real null-render startup checks reproduced 19.2 MHz with the old patch and 31.25
MHz with the corrected patch, equal to the external-NPDM path. Standard Eglantine
also passed this real-startup comparison. Unmodified PGO failed before log
initialization in this environment, so its full-startup comparison remains
unverified. Unit coverage adds legacy-patch recovery and metadata-reader slot
validation. See `EMULATOR_PATCH.md` and `native/check_emulator_startup.py`.

Local 1.5.0 passed all **49 synthetic tests and 16 frozen Windows XCI/NSP checks**, including nine PE/native-probe tests and the emulator patch dialog check. All six reviewed emulator GUI/CLI hook implementations were executed in isolated mappings with Switch 1/2 XCI, NSP and NCA fixtures (36 hook cases); apply/check/remove restored all six workspace copies byte-for-byte. Forward recognition also found the same loader code after non-code build-header changes, including relocated-address normalization in synthetic tests. Windows' own ImageHlp API validated all six patched PE checksums. Those automated checks used workspace emulator copies and synthetic inputs. See `EMULATOR_PATCH.md`.

Local 1.4.5 testing passed all 39 synthetic tests and all 16 frozen Windows XCI/NSP checks. Folder-path visibility and text/button separation were checked at 1160×830, 1010×780 and 1280×960. The GUI was also inspected visually. Linux shell syntax was checked, but no Linux runtime was available; Linux execution, GUI behavior and native binary compatibility remain unverified. These were local pre-release checks.

The release workflow requires all 51 synthetic tests, a Windows portable build, and 16 packaged-EXE checks covering PNG, WEBP, ICO and AVIF artwork in both XCI and NSP with single-file and package-folder output. Fixtures contain no game content.

Coverage includes payload and metadata round trips, integrity/corruption checks, source changes, cancellation cleanup, refusal to overwrite existing files, artwork crop/clipboard/drop behavior, companion preservation and explicit compatibility setup.

## Launch checks and their limits

Limited rendering checks were performed with PokeDinner 2.0.0 (commit `70ecb39ef0`) using the exact snapshot's external `main.npdm` companion and plaintext compatibility entries. Packages reached game screens. These checks do not establish full gameplay, performance, support for other emulator versions or companion-free booting.

Without that companion or the new emulator patch, the checked original loader selected the Switch 1 memory layout and clock before reading the embedded Switch 2 metadata. Exits/crashes were observed. This is a known limitation; passing package verification does not resolve it.

Earlier package checks established structural integrity and executable loading, not successful game boot. They should not be read as gameplay compatibility claims.

## Versions 1.4.3–1.4.4

A user reported booting without an external companion in PokeDinner 2.0.0 after selecting 12 GiB RAM. The original manual-test profile was also configured for 12 GiB; later failing tests used 4 GiB. This is evidence for a settings-dependent alternative, not automatic container detection or universal game support.

The same user subsequently reported considerably lower performance without the external companion. No controlled FPS comparison was performed. The caution recommends retaining the companion; package-folder output remains enabled by default.

The GUI now displays a startup caution with this guidance. Package-folder output is on by default and retains the companion workaround and report; unchecking it saves only the XCI/NSP. Automated coverage checks both modes, verification on/off, CLI behavior and remembered dismissal.

A clean Windows VM without Python was not available for the original portability checks. The EXE bundles its runtime, but compatibility with every Windows installation is not established.
