# Switch 2 Game Packager

[Download](https://github.com/smarkyie/switch2-game-packager/releases/latest) · [Build from source](BUILD.md) · [Changelog](CHANGELOG.md) · [Disclaimer](DISCLAIMER.md)

A portable Windows app that packages a complete, already-extracted ExeFS/RomFS snapshot into a plaintext XCI or NSP for compatible emulators. Choose a folder, add your own artwork, select the output format, and build.

**Piracy is not supported.** Use only files and artwork you have lawfully obtained and are authorized to use. No games, game artwork, firmware or Nintendo keys are provided. Nintendo Switch, Nintendo Switch 2 and related marks belong to Nintendo; game content belongs to its respective rights holders. This is an independent project, not affiliated with, sponsored by or endorsed by Nintendo. See [ownership and use notices](DISCLAIMER.md).

> **Caution — experimental software:** set emulator memory to **12 GiB** before testing Switch 2 packages. Booting without an external `main.npdm` was reported in PokeDinner 2.0.0 with that setting. Other games/builds may differ. Verification checks package integrity, not booting or gameplay. The packager does not change emulator memory settings.

A startup caution explains this before using the GUI. **Don't show this again** stores only a local preference under `%LOCALAPPDATA%\Switch2GamePackager\preferences.json`; the same guidance remains in **Notes & compatibility**. Command-line builds do not show a dialog.

**Performance caution:** considerably lower performance was reported when running without the external `main.npdm`, even with 12 GiB selected. Keep **Create package folder** enabled and retain its companion beside the game for the recommended setup. This is a user-reported observation, not a controlled benchmark or a guarantee for other games/builds.

Both output formats stream directly to their destination without an intermediate container. The app includes square artwork cropping, clipboard and drag-and-drop support, progress/cancellation, and full output verification.

## Quick start

1. Extract the entire ZIP to a writable folder.
2. Open `Switch2-XCI-Packager.exe`. Python is bundled; installation is not required.
3. Click **Browse folder** and select your main game dump folder, or drag the folder into the window. Pasting a folder path and pressing Enter also works.
4. Select the complete snapshot you want from the dropdown. The app reads its title ID from `main.npdm`.
5. Edit the displayed game name/version if needed. Add, drop or paste artwork, then click **Crop icon** to position it. Choose **XCI** or **NSP** in Output and select a destination filename. Switching formats retains the destination folder/name and updates its extension.
6. Leave **Verify after building** checked. **Create package folder** beneath it is on by default: a folder named after the output file contains the package, a metadata companion and JSON verification report. Uncheck it to save only the selected XCI/NSP. Then click **Build XCI** or **Build NSP**.

The app never overwrites an existing package and does not modify your source files. Cancellation removes the unfinished package. Verification works in both modes; it does not require saving a report. Allow roughly the input size plus 2% and 32 MB free disk space. Packages up to **32 GiB** are supported.

With **Create package folder** enabled, `D:\Packed\Game.xci` is saved as `D:\Packed\Game\Game.xci`, with `main.npdm` and `Game.xci.report.json` beside it. The companion is an optional workaround for the checked loader's early Switch 2 memory/clock detection. Keep each game/snapshot in a separate folder if using it; a conflicting companion is refused. The exact snapshot metadata is also embedded inside the package in both modes. An external companion is not always necessary: the 12 GiB setting allowed booting without it in the reported PokeDinner test.

XCI uses a gamecard-style wrapper; NSP uses a downloadable-content package wrapper. Both preserve the same game payloads and selected artwork. NSP has slightly less wrapper overhead; it is not compressed and does not improve gameplay speed. These outputs are unsigned plaintext emulator repacks. NSP support does not make them authenticated installable retail-console packages. Actual loading depends on the emulator fork's plaintext-content support.

## Accepted folder layouts

Direct snapshot:

```text
My Game/
  exefs/
    main
    main.npdm
    rtld, sdk, subsdk* ... (as present in your dump)
  romfs/
    ... complete game filesystem ...
```

Main folder with snapshots:

```text
My Game/
  base/
    exefs/...
    romfs/...
  updates/
    65536/
      exefs/...
      romfs/...
```

An empty `base` folder is fine when an update folder already contains the complete mounted game filesystem. A folder containing only update differences is **not** sufficient. Completeness cannot be reliably determined from filenames; select a snapshot you know is complete.

Separate updates and DLC are not automatically merged. DLC folders are left out. Multi-program applications, patch-only/BKTR data, encrypted NSP/XCI inputs, compressed ROM packages, decryption, and authenticated cartridge reconstruction are outside this release's scope. This is a snapshot packager, not an emulator or a universal game converter.

## Artwork and metadata

Artwork is exported as a **256×256 JPEG**, suitable for the emulator library icon. New artwork starts with a centered square crop. **Crop icon** opens an editor with drag-to-position, mouse-wheel/slider zoom, a live icon preview, Reset, Apply and Cancel. **Fit whole image** retains the entire image with padding instead. Cropping never changes the original file.

Supported inputs include PNG, JPEG/JFIF, WEBP, AVIF, GIF, TIFF, BMP/DIB, Windows ICO, Mac ICNS, TGA, PPM/PGM/PBM/PNM and JPEG2000. Animated or multi-page inputs use the first frame/page; icon containers use Pillow's selected image, normally the largest available. HEIC/HEIF and SVG are not decoded by this build.

Use **Paste** or **Ctrl+V** to add a copied bitmap, copied artwork file, or local image-file path. Ordinary text pastes in text fields continue to work normally. You can also drag one artwork file into the app. Clipboard images are held in temporary PNG files until the app closes; the app reads the clipboard only when you request a paste. Copying a URL alone does not download its image.

The app embeds the selected crop in either output format. No game artwork ships with this app.

If a standard `control.nacp` is present at the snapshot/main root or under `control/`, the app preserves it and updates uncompressed title text and the display version. Otherwise it generates basic control metadata. Generated fields are not a recreation of all original save-size, network, language, or DLC settings. A folder version such as `327680` is a numeric dump version, not necessarily a human-readable game version.

## Eglantine plaintext compatibility entries

Some Eglantine builds require key entries even when NCA headers and sections are plaintext. This package includes `compatibility/plaintext-repack.keys`, containing **locally generated placeholders**, not Nintendo keys. They cannot decrypt retail content. The app does not install them or change emulator configuration automatically.

If Eglantine reports **0007-0015** or a missing key for this app's plaintext images, close it and use **Notes & compatibility → Set up emulator keys folder…**. Select that profile's `keys` folder, commonly `%APPDATA%\eden\keys` or `user\keys` beside a portable emulator. Setup adds only missing plaintext placeholders to `prod.keys_autogenerated`, preserves existing entries and never writes `prod.keys`. An existing autogenerated file is backed up before appending; invalid existing entries are reported rather than replaced. Restart the emulator afterwards.

Manual export remains available:

1. Close Eglantine and open its user keys folder, commonly `%APPDATA%\eden\keys`.
2. If `prod.keys_autogenerated` does not exist, copy `plaintext-repack.keys` there and rename the copy to `prod.keys_autogenerated`.
3. If that file already exists, keep it. Back it up before editing and add **only missing** placeholder entries. Keep all real keys in `prod.keys`; that file takes precedence in the checked Eglantine loader.
4. Restart Eglantine.

The GUI's export button saves another copy without overwriting anything. Setup runs only when explicitly selected, never during scanning/building. These placeholders support this app's plaintext repacks; they do not replace your own retail keys for encrypted games. Eglantine forks can differ; consult the fork's documentation if its key-loading rules differ.

## Portability and privacy

- Windows 10/11 x64; no administrator rights, Python installation, emulator installation, or network connection required.
- The one-file EXE unpacks its bundled runtime into the Windows temporary directory at launch and cleans it up on normal exit.
- No telemetry, upload or automatic downloading. Emulator setup runs only when explicitly selected; builds do not change emulator configuration.
- When package-folder output is enabled, paths appear in its local JSON report. Review or remove reports before sharing them if you do not want to disclose local folder names.
- This release is unsigned. No claim of Nintendo authentication or endorsement is made.

## Source and redistribution

Full application source and synthetic tests are included under `source/` in the portable ZIP. In this repository, application modules are under `src/` and tests are at the root. The original application code is released under the MIT license in `LICENSE.txt`; third-party components retain their own licenses under `licenses/` and `THIRD_PARTY_NOTICES.md`.

You may redistribute the app and source with the required license notices. The software was developed with AI assistance. This package includes no Nintendo code, game data, artwork, console firmware, tickets, certificates, or Nintendo cryptographic keys. Use your own extracted data and artwork; redistribution rights for input/output content are separate from the app's license.

See `TECHNICAL_NOTES.md` for implementation details and `BUILD.md` (or `source/BUILD.md` in the portable ZIP) to rebuild the EXE. See `GITHUB_RELEASES.md` for publishing future versions.
