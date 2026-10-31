# Validation and compatibility

## Automated checks

The release workflow requires all 39 synthetic tests, a Windows portable build, and 16 packaged-EXE checks covering PNG, WEBP, ICO and AVIF artwork in both XCI and NSP with single-file and package-folder output. Fixtures contain no game content.

Coverage includes payload and metadata round trips, integrity/corruption checks, source changes, cancellation cleanup, refusal to overwrite existing files, artwork crop/clipboard/drop behavior, companion preservation and explicit compatibility setup.

## Launch checks and their limits

Limited rendering checks were performed with PokeDinner 2.0.0 (commit `70ecb39ef0`) using the exact snapshot's external `main.npdm` companion and plaintext compatibility entries. Packages reached game screens. These checks do not establish full gameplay, performance, support for other emulator versions or companion-free booting.

Without that companion, the checked loader selected the Switch 1 memory layout and clock before reading the embedded Switch 2 metadata. Exits/crashes were observed. This is a known limitation; passing package verification does not resolve it.

Earlier package checks established structural integrity and executable loading, not successful game boot. They should not be read as gameplay compatibility claims.

## Version 1.4.3

A user reported booting without an external companion in PokeDinner 2.0.0 after selecting 12 GiB RAM. The original manual-test profile was also configured for 12 GiB; later failing tests used 4 GiB. This is evidence for a settings-dependent alternative, not automatic container detection or universal game support.

The GUI now displays a startup caution with this guidance. Package-folder output is on by default and retains the companion workaround and report; unchecking it saves only the XCI/NSP. Automated coverage checks both modes, verification on/off, CLI behavior and remembered dismissal.

A clean Windows VM without Python was not available for the original portability checks. The EXE bundles its runtime, but compatibility with every Windows installation is not established.
