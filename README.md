# Bloody Roar II on Xbox — the UWP port

How to take the [BloodyRoar2Recomp](https://github.com/novapowers0/BloodyRoar2Recomp) static
recompilation of *Bloody Roar II* (PlayStation, 1999, `SCUS-94424`) and run it **on an Xbox Series X in
Developer Mode**, as a UWP package you build and sign yourself.

*(Español: [README.es.md](README.es.md))*

It is not a theory: the game boots, plays with a controller in menus and in a fight, in 16:9, with an
on-screen FPS counter toggled with **R3**. It has been playing on a real console since 2026-10-19.

## Which console this was tested on

**An Xbox Series X**, in Developer Mode. Read that literally:

- **Series X — tested.** Everything claimed here was measured on one.
- **Series S — never tested.** Not once. This port draws every frame on the **CPU** (there is no OpenGL
  in the App Container, so the runtime falls back to its software rasteriser), and the Series S has a
  slower memory subsystem and half the RAM budget for a game. It may run, it may run slower, or it may
  not hold a frame at all — nobody here knows, because nobody has tried. If you try it on a Series S,
  the frame rate you get is not the frame rate below.

## What this repository is

**A recipe and the tools that apply it.** The game project builds and runs beautifully on a PC, but its
framework did not carry **a single line** of UWP — not one mention of it in `runtime.cmake` — so
everything a console needs had to be written: thirteen guarded patches, an inert replacement for the
OpenGL backend, the WinRT entry point, and the build and packaging scripts. Everything here is applied
**to your own checkout** of the game project, on your machine.

## What this repository is **not**

It contains **no game code, no recompiled C, no disc image, no built executable, no `.msix` package and
no artwork**. It cannot produce a playable game on its own, and nothing you can download here is a game.
You need your own legally dumped copy of the disc and a working build of the game project first. See
[`NOTICE.md`](NOTICE.md).

The package tiles are **not** in here either: the ones on the real console were made from the game's own
art, which is Hudson Soft's. You supply your own — [`docs/ASSETS.md`](docs/ASSETS.md) lists the exact
sizes, and the packaging script stops with a clear message if the folder is empty.

## What you need first

| | |
|---|---|
| The game project | [novapowers0/BloodyRoar2Recomp](https://github.com/novapowers0/BloodyRoar2Recomp), cloned with `--recurse-submodules`, **building and running on your PC first** |
| Your own disc | An NTSC-U dump of `SCUS-94424` (`.bin` + `.cue`). **No retail BIOS needed**: the project ships OpenBIOS, which is free software, and that is what the package carries |
| Visual Studio | 2022, with the C++ build tools **and the C++ UWP component** (for `vcvarsall x64 uwp`, which is what links against the App Container CRT) |
| Windows SDK | For `makepri`, `makeappx` and `signtool` — the packaging script finds the newest one you have |
| CMake and Ninja | The generator is **Ninja**: Visual Studio's is multi-config and this framework writes one version file per config, which CMake refuses |
| Python 3 | For the patches. Nothing but the standard library |
| An Xbox Series X in Developer Mode | And a certificate to sign with — a self-signed one is fine ([`docs/INSTALL.md`](docs/INSTALL.md) §3) |

SDL2 2.30.2 built for `WindowsStore` is a prerequisite, not a download: SDL3 has no WinRT backend.
[`docs/INSTALL.md`](docs/INSTALL.md) §2 builds it in four commands.

## How it goes

Three commands. [`docs/INSTALL.md`](docs/INSTALL.md) is the long version of these, including the console
side.

> **Where to type this:** in **PowerShell** — press the **Windows** key, type `powershell` and press
> **Enter** — in an **ordinary** window: you do not need "run as administrator", and using it would
> break the signing step, because the certificate lives in the store of whoever runs the command. From
> this repository's folder.

```powershell
# 1. patch your checkout of the game project (idempotent, all-or-nothing, atomic)
python tools\apply_uwp.py <path-to-game-project-root>

# 2. configure and build for the console
powershell -ExecutionPolicy Bypass -File tools\configurar-uwp.ps1 `
    -Raiz <path-to-game-project-root> -Build <build-folder> -Sdl2 <SDL2 cmake folder> -Compilar

# 3. package and sign (your own tiles, your own certificate)
powershell -ExecutionPolicy Bypass -File tools\empaquetar-uwp.ps1 `
    -Build <build-folder> -Salida <output-folder> -Certificado <your certificate thumbprint> -Version 1.0.0.0
```

`python tools\apply_uwp.py --list` prints the thirteen steps and what each one solves.

Then install the `.msix` through the Device Portal and upload your disc, **split into parts**, to the
app's data folder. Step by step: **[`docs/INSTALL.md`](docs/INSTALL.md)**
([en español](docs/INSTALL.es.md)).

## What it had to solve

Every one of these was a real failure on the console, and most of them hid the next. The detail, with
what the log said in each case, is in **[`docs/HOW-IT-WORKS.md`](docs/HOW-IT-WORKS.md)**.

| | Symptom | Fix |
|---|---|---|
| 1 | No UWP build at all | The framework had no console profile. One is added to `runtime.cmake`, switched on only when `CMAKE_SYSTEM_NAME` is `WindowsStore` |
| 2 | The package installed and the console would not launch it | `OPENGL32.dll`: merely *importing* it is enough. The GL backend is replaced by an inert one and the runtime keeps to its software rasteriser |
| 3 | `SDL_CreateWindow failed: Could not initialize OpenGL` | The runtime detects that GL is unavailable, but after asking SDL for a GL window. The software renderer is now chosen *before* the window is created |
| 4 | Linker errors in App Container | `MessageBoxA`, `GetOpenFileNameA`, `SetErrorMode`, DbgHelp, `CreateProcess`, `TerminateJobObject`, `CreateFiber` — none exist there. Each one is guarded or routed to the path the framework already has for other systems |
| 5 | `C atomic support is not enabled` | The framework passes `/experimental:c11atomics` to the one file it knew about; a second one needs it too |
| 6 | `fatal error RC1107: invalid usage` | The resource compiler chokes on the project's defines. In UWP the icon comes from the package Assets anyway |
| 7 | `LNK2019` on `SDL_main` | With netplay off, the lobby registration is still called, unguarded — a framework bug, not a UWP one |
| 8 | `LNK2019` asking for `main(Platform::Array<String^>^)` | A UWP app does not start at `main()`. SDL's WinRT entry point, compiled with `/ZW` |
| 9 | `-DPSX_SETUP_WIZARD=OFF` did nothing | The game's CMake sets it with `FORCE`, which overrides the command line |
| 10 | Nothing could be written: saves, logs, config | The runtime anchors every file next to the executable, which in UWP is the read-only install folder. It now anchors in the app's data folder |
| 11 | `savestate: SAVE FAILED … \WindowsApps\…` | A second, separate path: `memcard_dir` was relative and resolved against the read-only folder |
| 12 | The controller did nothing | With no launcher to assign a device, player 1 defaults to **keyboard**, silently. Both slots go to `auto` |
| 13 | No way to read the frame rate | A console has no title bar, which is where the runtime writes it, and the on-screen layer only compiled with the launcher. Counter on screen, **R3** toggles it |
| 14 | `cannot launch with selected mods: package does not target this game/image` | Mods — and the disc digest each one requires — are validated *before* the disc is resolved. Fatal here, because widescreen ships on and its manifest carries the disc's SHA-256 |
| 15 | The disc would not upload: HTTP 500 | Portal uploads go through `D:\DevelopmentFiles`, which is small and usually nearly full. The disc goes up in 150 MiB parts and the entry point joins them on first boot |

## What is not solved

Two things, stated plainly because finding them out the hard way is worse:

- **It does not hold 60 FPS everywhere.** 60 almost all the time, but it drops to **55 and as low as
  50** in some stages and fights; the log reads **52–54 fps** during the game's own attract demo, which
  is the heaviest scene, and **59.0** on light screens. Two separate things are going on, and
  [`docs/HOW-IT-WORKS.md`](docs/HOW-IT-WORKS.md) §7 has the measurements: a fixed 0.98x that is the
  wall-clock pacer, not missing power, and the real drops, which are the software rasteriser running out
  of time. ⚠ Forcing the cadence to 60 Hz so the driver's vsync would rule it **makes it worse** — 48.0
  fps in the same window — because a frame that misses 16.67 ms loses the whole refresh. That was tried,
  measured and reverted.
- **It does not come back where you left it.** In Developer Mode an Xbox *terminates* a game that goes
  to the background, so coming back from Home restarts it. The framework's save-state machinery is
  there and works; wiring it to the activation state is not done in this port.

Both are open issues on this repository.

## How the recipe was verified

What makes this repository credible is not that it builds, but that **applied to a clean clone it leaves
the tree the shipped package was built from**:

- clean clone of the game project at the commit the package came from, framework submodule at its pin;
- `apply_uwp.py` end to end, twice (the second pass changes nothing — every step is idempotent);
- the ten files it touches, compared against the reference tree: **one identical byte for byte**, eight
  identical except for comments, and `runtime.cmake` identical except for three CMake messages. The
  comments and the messages are in English here, like the rest of the runtime, which is the one change
  made on purpose; the reference tree had them in Spanish.
- the inert GL replacement passes `clang -fsyntax-only -Wall -Wextra` without a warning.

The numbers and what else was *not* re-measured are in [`docs/HOW-IT-WORKS.md`](docs/HOW-IT-WORKS.md).

## Credits and license

Port and tooling by **Recompilaciones**. Released under the
[PolyForm Noncommercial License 1.0.0](LICENSE), matching the license of the psxrecomp framework this is
a derivative of.

The patch scripts carry their comments in Spanish, which is where they were written; what they write
*into* the game tree is in English, like the rest of the runtime. The documentation is in both languages.

*Bloody Roar II* is © Hudson Soft / Eighting. This project is not affiliated with them, with Konami, with
Sony, with Microsoft, or with the authors of the game project or the framework, and it distributes
nothing that belongs to them. The details — exactly what is and is not included here, how much of other
people's work is quoted, and how to ask for a takedown — are in [`NOTICE.md`](NOTICE.md). Rights holders
can write to **jajdpmail@gmail.com**.
