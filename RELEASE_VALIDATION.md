# Validation and compatibility

## NSP Box 3.0

The release requires all **64 unit/UI/native tests**, **nine frozen NSP packaging
cases** and a **four-drop frozen native file-drop/clean-shutdown check**. Fixtures
are synthetic and contain no game data. PNG, WEBP, ICO and AVIF artwork are checked
in single-file and package-folder game modes, plus a separate DLC NSP case.

The drag-and-drop crash in issue #2 was reproduced on Windows in the real Tk
mainloop before the fix. Native callbacks now queue paths without calling Tcl/Tk;
normal Tk timers handle the dropped files. Regression coverage includes repeated
folder/image drops and Unicode WEBP filenames.

The Game/DLC tabs and emulator patch dialog were inspected visually. UI checks
cover minimum-size control visibility, artwork paste/crop, tab transitions, icon
cache reuse, gradient layering, reduced-motion behavior and timer cleanup.
The ambient layer shares one Tk image across canvases and pauses when minimized.
All 22 PNG assets have RGBA transparency and no embedded PNG metadata.

## Emulator patch checks

All 16 exact Windows x64 GUI/CLI profiles have patch/remove restoration coverage.
The ten added executable variants passed exact restoration and 60 isolated native
hook cases. Standard Eglantine 98/build-99 and PokeDinner 2.1.0a startup comparisons
selected 31.25 MHz with the patch, matching their external-companion paths.
Unmodified PGO CLI startup failed with 0xC0000008 in the test environment, so full
PGO startup or gameplay compatibility is not claimed. No emulator binaries ship
with NSP Box. See [supported targets and limits](EMULATOR_PATCH.md).

## Real-world limits

A user installed a Bananza DLC NSP in PokeDinner 2.0.0 and confirmed in-game
recognition. This is one successful test, not universal DLC compatibility.
Actual game data and original title IDs are required; generated metadata cannot
recreate missing game services or original required-update information.

Set emulator memory to 12 GiB before testing Switch 2 packages. Without the patch,
an external exact `main.npdm` can still be needed for the checked loader's early
Switch 2 memory/clock selection. 12 GiB alone may boot with incorrect timing and
reduced performance. Integrity checks do not guarantee booting, gameplay or FPS.

Windows x64 is the only shipped binary target. A clean Windows installation
without Python and every graphics driver/emulator configuration have not been
tested. This is experimental software with limited real-world testing; please
[report reproducible problems](https://github.com/smarkyie/switch2-game-packager/issues/new).
