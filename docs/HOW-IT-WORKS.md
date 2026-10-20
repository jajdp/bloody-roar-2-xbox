# How it works, and what it cost

*(Español: [HOW-IT-WORKS.es.md](HOW-IT-WORKS.es.md))*

Thirteen patches, one replacement source file and a WinRT entry point. This is what each one is for,
what the console said before it, and what was measured. The order here is the order
[`../tools/apply_uwp.py`](../tools/apply_uwp.py) applies them in, and that order was verified, not
guessed — see §9.

Everything measured here was measured on an **Xbox Series X** in Developer Mode. Nothing has ever been
run on a Series S.

## 0. The starting point: a framework with no console in it

The game project builds and plays on Windows. Its framework — `psxrecomp`, as the project pins it — had
**not one mention of UWP** in `runtime.cmake`. For comparison, the sister port of another psxrecomp game
found 28 mentions in its own framework fork, because that fork's author had started the work. Here,
there was nothing: no profile, no guards, no stub for the parts of Windows an App Container does not
have.

So the first patch is not a fix, it is a profile. `parche_uwp.py` adds to `runtime.cmake`:

- `PSX_UWP`, switched on only when `CMAKE_SYSTEM_NAME` is `WindowsStore`;
- no debug server (its TCP socket is not allowed), no launcher, no Vulkan;
- SDL2 through a CMake package, because SDL3 has no WinRT backend;
- `PSX_UWP=1` for the compiler, which is what every guard below hangs off;
- `/APPCONTAINER` on the link, and `SDL_MAIN_HANDLED` off, which is what lets the WinRT entry point be
  the entry point.

Its four anchors survived **583 lines of change** in that one file between the framework revision the
sister port used and the one this game pins. That is the argument for anchors over line numbers.

## 1. "Failed to launch the application"

The package installed, appeared in the list, and did nothing when launched. No log, no window, no error
beyond that one line in the portal. There were two causes, and the first hid the second.

**The App Container CRT.** Built with `vcvars64`, the executable imports `msvcp140.dll` and
`kernel32.dll` — the desktop CRT. A console has the `_app` variants, through the VCLibs framework
package. `vcvarsall x64 **uwp**` is what puts `lib\x64\store` on `LIB`, and that is why
[`INSTALL.md`](INSTALL.md) §5 insists on it.

**`OPENGL32.dll`.** This one is worth stating plainly, because it is invisible: *merely importing* a DLL
the console does not have is enough for the system to refuse to activate the app. The runtime's GL
backend calls GL 1.x directly, so the import was there. The fix is
[`../src/gpu_gl_renderer_stub.c`](../src/gpu_gl_renderer_stub.c), a replacement translation unit that
defines the same symbols, all inert, so everything else links unchanged and the runtime keeps to its
software rasteriser — which is what it uses on a console anyway. `dbghelp` and `comdlg32` went the same
way: in UWP nothing needs to be linked by name, because `WindowsApp.lib` is the umbrella library CMake
adds for `WindowsStore` and it already carries what is allowed, sockets included.

The replacement passes `clang -fsyntax-only -Wall -Wextra` without a warning. It has one function the
sister port's did not need: `gl_renderer_set_scanlines`, which this framework's present path calls.

## 2. `SDL_CreateWindow failed: Could not initialize OpenGL / GLES library`

With GL gone, the next boot got further and died here. The runtime *does* detect that GL is unavailable
and says so — `renderer = opengl requested but unavailable — falling back to software` — but that
happens **after** the window is created, and the preference it reads when creating it still said
`opengl`, so SDL was asked for a GL window. `parche_uwp_render_software.py` fixes the renderer to
software in the UWP profile, before the backend is chosen.

## 3. Everything the App Container does not have

Five separate link or compile failures, each found by fixing the previous one. They are all in
`parche_uwp_codigo.py` and `parche_uwp_codigo_br2.py`:

| What | Why it is not there | What the patch does |
|---|---|---|
| `MessageBoxA` | No dialogs in an App Container | The two warnings go to the log only |
| `GetOpenFileNameA` / `OPENFILENAMEA` | Same, and there would be nowhere to open a file picker on a TV | Guarded out |
| `SetErrorMode` + `SEM_*` | Not exported | Guarded out; it only suppressed a Windows error box that does not exist there |
| DbgHelp (`SymInitialize`, `StackWalk64`, `SymFromAddr`) | Not available, and walking another thread's stack is not allowed | The main-thread stack dump returns `[]`. The freeze heartbeat still writes everything else — same as a PC where symbols cannot be resolved |
| `CreateProcess`, handle inheritance, `TerminateJobObject` | Not available | On-the-fly recompilation falls into the branch the framework already has for other systems: `manual compile flow only`. There is no compiler to spawn on a console |
| `CreateFiber` / `ConvertThreadToFiber` | Only the `…Ex` variants are exported | A console branch, selected by `WINAPI_FAMILY`, using `CreateFiberEx` and `ConvertThreadToFiberEx`. Fibers are the BIOS scheduler's engine, so this is not optional |

And two that are **not** UWP's fault:

- **`C atomic support is not enabled`.** The framework passes `/experimental:c11atomics` "scoped to the
  one C source that needs it". A second file needs it too — the starvation guard — and MSVC stops. Both
  are the only two `.c` in the runtime that include `<stdatomic.h>`.
- **`LNK2019` in `SDL_main`.** With netplay off, the lobby client is not compiled, but the runtime still
  calls its registration function, unguarded. That is a framework bug that only shows up in a build
  without netplay; the patch guards the call.

## 4. `fatal error RC1107: invalid usage`

The resource compiler, invoked for the executable's icon, chokes because CMake passes it the project's
`-D` defines and the window title contains spaces and parentheses. In UWP the icon comes from the
package Assets, so the Windows branch is simply excluded from the console profile; the PNG is still
copied next to the executable, as before.

## 5. Nothing could be written, and in two different ways

The runtime anchors **every** file — config, disc, BIOS, memory cards, caches, logs — in the directory of
the executable, and says so in its own comment: *"Deliberately NEVER the current working directory"*. In
UWP that directory is the package install folder, which is read-only.

`parche_uwp_rutas.py` makes that function return the app's data folder when building for the console,
which is where the Device Portal can put things and where writing works. It derives it from the
package's own Temp path (`…\AC\Temp`, two levels up) so that nothing has to initialise the Windows
Runtime before SDL.

That was not enough, and the second half is the kind of thing only a real run finds. The log said:

```text
savestate: SAVE FAILED slot 99 -> S:\Program Files\WindowsApps\<package>\saves/scph1001/state_….pst
```

`game_us.toml` is loaded from the install folder, and its `[runtime] memcard_dir = "saves"` is a
**relative** path, resolved against the folder of that file. So the memory cards and the save states
pointed at a read-only place — a path that had already been resolved before the anchor patch could do
anything about it. `parche_uwp_escritura.py` re-anchors it in the data folder once it is resolved.

## 6. The controller did nothing, silently

The game reached the title screen and the pad did nothing. Nothing in the log either, which is what made
it slow: the runtime assigns each player's device from `[controller] device`, and with no settings the
factory default in a product build is **keyboard** for player 1 — because on a PC the launcher writes
the chosen device before the game starts. On a console there is no launcher and no keyboard, and the
message that would have told you (`opened controller for slot`) is only printed for players whose type
is a pad.

`parche_uwp_mando.py` leaves both slots on `auto` — the first pad connected — when building for the
console, and [`../config/settings.toml`](../config/settings.toml) ships the same defaults, in digital
mode, which is how this game is played.

## 7. The frame rate: what is known, measured, and still open

A console has no title bar, which is exactly where the runtime writes the frame rate. And the on-screen
layer that could show it — `host_osd.c`, with its own 8×8 font — was behind `#if defined(RECOMP_LAUNCHER)`,
so it only compiled when the product carried the launcher. Two patches: `parche_uwp_osd.py` compiles that
layer for the UWP profile too (it needs nothing from the launcher), and `parche_uwp_fps_encendido.py`
turns the counter on by default, because the framework's own switches for it are an environment variable
and a keyboard shortcut, and a console has neither.

`parche_uwp_fps_r3.py` binds **R3** — clicking the right stick — to toggling it. That button is safe: the
pad runs in digital mode, where the DualShock's stick clicks do not exist, so the game never sees it.

⚠ **Where the check goes is the trap**, and it was paid for twice: in SDL's event loop it does not work
(that loop is the pump that keeps the window alive, and the button event does not arrive there), and
inside the function that builds the pad word for the game it does not work either (it is not walked every
frame). It sits on the pad word, before the SIO, which is.

### What the counter then showed

| Scene | Measured | Ratio |
|---|---|---|
| Light screens (menus, loading) | **59.0 fps** | 0.98x |
| The game's own attract demo — the heaviest scene | **52–54 fps** | 0.88–0.90x |
| Playing | 60 almost always, dropping to **55 and as low as 50** in some stages and fights | — |

**These are two different problems, and only one of them is about power.**

- The **fixed 0.98x** is the pacer. SDL/WinRT does not tell the runtime the panel's refresh rate — the
  log says `host refresh unknown` — so it paces frames off the wall clock, and that drifts by about 2%.
  It is not missing performance.
- The **drops to 50–56** are real: the software rasteriser does not finish the frame in time in the
  heaviest scenes.

⚠ **One fix was tried, measured and reverted.** Forcing the cadence to 60 Hz so the driver's vsync would
rule the pacing gave **48.0 fps (0.80x)** in the same measurement window, against the 52–54 of the
wall-clock pacer. The reason is simple once you see it: a frame that misses the 16.67 ms budget loses the
*whole* refresh, so the penalty is quantised. It is in this document rather than in the repository
because knowing what does not work is worth as much as the recipe.

The way forward is to make drawing cheaper — measure where the time goes, add fast paths to the
rasteriser, take work out of the hot path — which is what a sister port of this family did to get a
sustained 60. That work is not done here, and it is an open issue.

## 8. The mods, the disc, and the order they happen in

The framework validates mod packages — and the disc digest each one requires — **before** it resolves
where the disc actually is: `mod_runtime_commit(resolved_disc)` runs before `resolved_disc` holds the
real path. On a PC that is harmless, because by then it carries whatever the project's `game_us.toml`
has written in it. On a console that path cannot exist: the disc lives in the package's data folder and
its path depends on the install, so the packaging step removes the key.

The result was that the mod system hashed an empty disc and refused to launch:

```text
psxrecomp: cannot launch with selected mods: package does not target this game/image: br2.enhancement.widescreen
```

And here that is fatal rather than annoying, because widescreen ships **on** — there is no Mods tab on a
console to tick it in — and its manifest carries the disc's SHA-256 for all three regions.
`parche_uwp_disco_mods.py` resolves the disc from the `disc.cfg` sidecar right before the check.

⚠ **Its anchor is not the sister port's.** Between the two framework revisions the netplay block was
rewritten entirely, and the inherited anchor matched *zero* times. The call is still in the same place,
but it now hangs off an if-else with the launcher's netplay plan. This is the most useful kind of patch
failure: it stopped, named the file and the count, and wrote nothing.

## 9. The disc does not go in the package

Portal uploads are staged through `D:\DevelopmentFiles`, a ~5 GB partition that is usually nearly full,
and a 527 MiB upload answers HTTP 500. `tools/partir_disco.py` cuts the `.bin` into 150 MiB parts — four
for this game — and the WinRT entry point joins them on the next boot, once, logging
`partes: 4 unidas, 552729408 bytes`. That number is the exact size of the dump, which is the point of
printing it.

The entry point, [`../src/SDL_winrt_main_NonXAML.cpp`](../src/SDL_winrt_main_NonXAML.cpp), is SDL's own
(public domain, David Ludwig) with that and a few other things added in place: seeding the data folder
from the package on every boot, writing `bios.cfg` and `disc.cfg` with absolute paths, redirecting the
runtime's output to logs the portal can read, recording how the app was activated, and asking SDL to
handle the **B** button so the system does not take it as "back" and close the game.

⚠ **Three values of another game were hiding in it**, inherited from the sister port, and all three fail
silently rather than loudly. They are listed here because anyone porting this recipe to a *third* game
will meet exactly the same three: the **serial** in the entry point (it creates the data folder under the
wrong name), the **data subfolder** in the paths patch (the runtime looks for its files where they are
not), and the **seed list** in the entry point (this game has one config per region, so `game_us.toml`
has to be in that list or its configuration is never seeded).

## 10. How the recipe was verified

The claim is not "it compiles". The claim is **this recipe produces the tree the tested package was
built from**, and it was checked like this:

1. A clean clone of the game project at `eed1e8d1`, framework submodule at `219a3627`.
2. The chain applied to it — first with the project's own scripts, to establish what the reference tree
   is; then, on another clean clone, with this repository's published scripts.
3. The **ten files the chain touches**, compared byte for byte:
   - against the reference tree, the project's own chain gives **9 of 10 identical**. The tenth is
     `main.cpp`, which differs by exactly **3 bytes**: a UTF-8 BOM that the development tree had picked
     up along the way.
   - against that result, this repository's chain gives **one identical byte for byte**, **eight
     identical except for comments**, and `runtime.cmake` identical except for **three CMake messages**.
     The comments and the messages are in English here, like the rest of the runtime, which is the one
     change made deliberately. The published patches also stop adding that BOM to the five framework
     files that had gained one.
4. `git status` on both clones lists the *same ten paths* and nothing else, so the recipe touches
   nothing it does not declare.
5. The whole chain run **twice**: the second pass writes nothing and says so. Every patch is idempotent,
   all-or-nothing and atomic (a `.tmp` beside the file, then one atomic replace).
6. `clang -fsyntax-only -Wall -Wextra` on the GL replacement: no warnings.

### What was not re-measured, and why

- **The UWP build and the package itself.** Rebuilding them needs the 68 MB of C generated from a disc
  and the UWP toolchain; what is published is the recipe, and the binary that came out of it is the one
  that has been playing on a console since 2026-10-19.
- **Anything on a Series S.** Never tried. See the README.
- **The 60 FPS fix**, because there is not one yet (§7).
