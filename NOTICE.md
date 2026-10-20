# Notice

*(Español: [NOTICE.es.md](NOTICE.es.md))*

## Not affiliated

This is an unofficial, noncommercial fan project. It is **not affiliated with, endorsed by or connected
to Hudson Soft, Eighting, Konami, Sony or Microsoft**, or any of their subsidiaries, nor to the author of
the [psxrecomp](https://github.com/RetroPortingToolKit/psxrecomp) framework or to the author of the
[game project](https://github.com/novapowers0/BloodyRoar2Recomp) this port is built on. *Bloody Roar*,
*Xbox* and all related names and marks are the property of their respective owners, and are used here
only to say what this works with.

Nothing here is for sale, and nothing here is monetized.

## What this repository does not distribute

No game code. No disc image. **No recompiled C** — the 56 files and 68 MB of C that make this game run
are generated from *your* disc, on your machine, by the game project's own recompiler; they are the
game's code and they never come from here. No built executable. No `.msix` package. No save data. No
artwork, audio, music or fonts from the game — not even the package tiles, which is why
`package/Assets/` is empty and [`docs/ASSETS.md`](docs/ASSETS.md) asks you to supply your own.

No BIOS either, and none is needed: the game project ships OpenBIOS, which is free software, and that is
what the package carries.

Nothing here produces a playable game on its own. You need your own legally dumped copy of the disc and
a working build of the game project, neither of which this repository provides or can provide.

## What it does contain of other people's work

Measured, file by file, against the two upstream trees at the revisions this port was built from: **77
lines in 33 anchors**. An anchor is the text a patch checks before writing, so that it fails safely
instead of corrupting a tree it does not recognise.

| Whose | Lines | Anchors | Where |
|---|---|---|---|
| The psxrecomp framework | **70** | 31 | `runtime.cmake` (16), `main.cpp` (37), `host_osd.c` (5), `autocompile.c` (5), `freeze_heartbeat.c` (4), `psx_fiber.c` (2), `crash_trace.c` (1) |
| [novapowers0/BloodyRoar2Recomp](https://github.com/novapowers0/BloodyRoar2Recomp) | **7** | 2 | `CMakeLists.txt`, in `tools/parche_uwp_cmake_juego.py` |

**The framework** the game uses is [novapowers0/psxrecomp](https://github.com/novapowers0/psxrecomp)
(branch `nova-mods`), a fork of
[RetroPortingToolKit/psxrecomp](https://github.com/RetroPortingToolKit/psxrecomp). It carries the
**PolyForm Noncommercial License 1.0.0**, © 2026 Matthew Stan, which permits noncommercial derivative
works. This repository is such a derivative and is released under [that same license](LICENSE) — the
canonical text from [polyformproject.org](https://polyformproject.org/licenses/noncommercial/1.0.0),
with its `Required Notice`.

**The game project** carries the **MIT License**, © 2026 BloodyRoar2Recomp contributors, which is why
the seven lines of its `CMakeLists.txt` can be quoted at all. MIT asks that its notice travel with
substantial portions of the software; seven lines of build script in a patch anchor is not that, and no
file of that project is reproduced here, but it is named and linked wherever it is quoted, and this is
the notice.

**`src/SDL_winrt_main_NonXAML.cpp`** is SDL's WinRT entry point, *placed in the public domain by David
Ludwig*, with what this port needed marked inside it: seeding the app's writable data folder, joining
the disc uploaded in parts, writing the `bios.cfg` / `disc.cfg` pointers, redirecting the runtime's
output to a log the Device Portal can read, recording why the app was started, and keeping **B** from
closing the game. The original is part of [SDL](https://github.com/libsdl-org/SDL).

**`src/gpu_gl_renderer_stub.c`** is ours. It defines the same symbols as the framework's OpenGL backend,
all inert, so the rest of the runtime links unchanged while GL stays unavailable; the names and
signatures come from the framework's own public header, which is what any replacement of an interface
has to match.

**There are no screenshots here at all.** A screenshot of this running would be mostly Hudson Soft's
artwork, and it would be showing their work rather than this one.

## Takedown and contact

If you hold rights in this material and want something here removed or changed, write to
**jajdpmail@gmail.com**, saying what you object to and in what capacity you are writing.

Requests from rights holders are honoured: the disputed part is removed, or the repository is taken down,
without argument, and you will get a reply confirming it. No notice or legal process beyond that email
is needed to reach the person who maintains this.
