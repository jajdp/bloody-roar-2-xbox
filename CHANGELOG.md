# Changelog

All notable changes to this repository. Dates are `YYYY-MM-DD`.

The versions here are **the repository's**, not the package's. The package version is whatever you pass
to `empaquetar-uwp.ps1 -Version`, and it has to go up on **every** package you install, because
installing the same version on top of itself unregisters it.

## [1.0.1] — 2026-10-20

### Fixed

- **`tools/empaquetar-uwp.ps1` asked for a tile the package does not use.** It worked out which PNGs
  the manifest needs with a regular expression over the whole file, and that also matches the ones
  inside an **XML comment** — `Wide310x150Logo.png` is in one, because the wide tile is optional and
  its line ships commented out. So the first thing the script did was stop and ask for a fifth tile
  that nothing references. It now reads the XML's attributes and text nodes (`Square150x150Logo="…"`
  and `<Logo>…</Logo>`), where tiles actually live; a comment is neither, so it cannot be mistaken for
  a requirement. The four it asks for are the four the manifest names.

  Found by running the check rather than reading it, which is the only way this kind of thing shows up.

## [1.0.0] — 2026-10-20

First publication. The recipe for the UWP port, as it was applied to the build that has been playing on
an **Xbox Series X** in Developer Mode since 2026-10-19: controller, 16:9 on by default and an on-screen
FPS counter toggled with **R3**.

### Added

- **Thirteen guarded patches**, orchestrated by `tools/apply_uwp.py`, each one idempotent,
  all-or-nothing and atomic: the UWP profile the framework did not have, the inert OpenGL replacement,
  the App Container guards (dialogs, `SetErrorMode`, DbgHelp, `CreateProcess`, fibers), the C11 atomics
  of a second source file, the icon resource, the unguarded netplay lobby registration, the game CMake's
  two `FORCE`s and its WinRT entry point, the data folder and the writable state, the controller
  defaults, the on-screen layer and the FPS counter with its R3 toggle, and resolving the disc before the
  mods are validated.
- **`src/SDL_winrt_main_NonXAML.cpp`** — the WinRT entry point: seeds the data folder from the package,
  joins the disc uploaded in parts, writes the `bios.cfg` / `disc.cfg` pointers, redirects the runtime's
  output to readable logs, records how the app was activated, and keeps **B** from closing the game.
- **`src/gpu_gl_renderer_stub.c`** — the inert replacement for the GL backend, so the executable does not
  import `OPENGL32.dll`, which by itself stops the console from activating the app. It compiles with
  `-Wall -Wextra` without a warning.
- **`tools/configurar-uwp.ps1`** and **`tools/empaquetar-uwp.ps1`** — configure and build with Ninja in
  the UWP toolchain; package, sign, and seed `mods/state.toml` with widescreen on, because a console has
  no Mods tab. Everything they need comes in by parameter: the tree, the build folder, the SDL2 package,
  the version, your certificate, your tiles.
- **`tools/partir_disco.py`** — the disc in 150 MiB parts, because the Device Portal answers 500 to the
  whole thing.
- **`config/settings.toml`** — the factory settings for a console: both pads on `auto` in digital mode,
  no launcher, software rendering left to the runtime's own fallback.
- **Documentation in both languages**: a build-and-install guide that says which terminal each command
  goes in, whether administrator is needed (it is not, and in one step it breaks things), and how the
  console has to be set up — including that **with no profile signed in the console will not launch
  apps**. Plus `HOW-IT-WORKS`, with every failure that had to be solved, what the log said, and the frame
  rate measurements.
- **`NOTICE`** — what is and is not here, with the quoting measured file by file: 77 lines in 33 anchors,
  70 of them from the framework (PolyForm Noncommercial) and 7 from the game project (MIT).

### Known limitations, stated up front

- **It was tested on an Xbox Series X only.** A Series S has never been tried, and this port draws every
  frame on the CPU, so nothing about its frame rate can be assumed there.
- **It does not hold 60 FPS everywhere**: 60 almost always, 55 and as low as 50 in heavy stages.
  `HOW-IT-WORKS` §7 separates what is the wall-clock pacer (a fixed 0.98x) from what is really the
  software rasteriser, and records the one fix that was tried and reverted because it measured worse.
- **It does not resume after the console terminates it.** Going to Home restarts the game. The
  framework's save-state machinery works; wiring it to the activation state is not done here.

### Not included, on purpose

- The disc, the built executable, the `.msix`, the saves and the package tiles.
- **The recompiled C** — 56 files, 68 MB — because it is the game's own code, generated from your disc
  by the game project's recompiler, on your machine.
- The diagnostics and measuring scaffolding that produced the numbers in `HOW-IT-WORKS`: they were
  development tools, not part of the port.
