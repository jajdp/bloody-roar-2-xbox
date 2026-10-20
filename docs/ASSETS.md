# The package tiles

*(Español: [ASSETS.es.md](ASSETS.es.md))*

A UWP package needs its tiles. **This repository ships none of them**: the ones used on the real console
were cut from the game's own artwork, which belongs to Hudson Soft, and that is exactly what
[`NOTICE.md`](../NOTICE.md) promises not to distribute. You supply your own.

`tools/empaquetar-uwp.ps1` reads `package/Package.appxmanifest`, works out which PNGs it names, and stops
before doing anything if one of them is missing — telling you which.

## What to put in `package/Assets/`

The four the manifest names, which are the ones the build actually requires:

| File | Size |
|---|---|
| `SplashScreen.png` | 620 × 300 |
| `Square150x150Logo.png` | 150 × 150 |
| `Square44x44Logo.png` | 44 × 44 |
| `StoreLogo.png` | 50 × 50 |

And the scaled variants a complete package carries. They are optional for the build, but without them
the console upscales the base ones:

| File | Size |
|---|---|
| `SplashScreen.scale-200.png` | 1240 × 600 |
| `Square150x150Logo.scale-200.png` | 300 × 300 |
| `Square44x44Logo.scale-200.png` | 88 × 88 |
| `Square44x44Logo.targetsize-24_altform-unplated.png` | 24 × 24 |
| `StoreLogo.scale-200.png` | 100 × 100 |
| `LockScreenLogo.png` | 24 × 24 |
| `LockScreenLogo.scale-200.png` | 48 × 48 |

PNG, 32-bit with alpha. The sizes are not advisory: a tile of the wrong size makes `makepri` produce a
resource index the console will not accept.

`Wide310x150Logo.png` (310 × 150) is **optional and commented out** in the manifest: the console does not
use it in Developer Mode, and referencing a PNG that does not exist makes `makepri` and `makeappx` fail.
If you want one, add the file and uncomment the `uap:DefaultTile` line.

## The quickest way to have something that works

Any images of those exact sizes will do — the console only needs them to exist and to be the right
shape. With ImageMagick, if you have it, all eleven come out in one go.

> **Where to type this:** in **PowerShell** — press the **Windows** key, type `powershell` and press
> **Enter** — in an **ordinary** window: you do not need "run as administrator", from this repository's
> folder.

```powershell
$tiles = @{
  'SplashScreen.png'                                   = '620x300'
  'SplashScreen.scale-200.png'                         = '1240x600'
  'Square150x150Logo.png'                              = '150x150'
  'Square150x150Logo.scale-200.png'                    = '300x300'
  'Square44x44Logo.png'                                = '44x44'
  'Square44x44Logo.scale-200.png'                      = '88x88'
  'Square44x44Logo.targetsize-24_altform-unplated.png' = '24x24'
  'StoreLogo.png'                                      = '50x50'
  'StoreLogo.scale-200.png'                            = '100x100'
  'LockScreenLogo.png'                                 = '24x24'
  'LockScreenLogo.scale-200.png'                        = '48x48'
}
foreach ($t in $tiles.GetEnumerator()) {
  magick -size $t.Value xc:"#1b1b1f" (Join-Path 'package\Assets' $t.Key)
}
```

Replace them with real art whenever you like: nothing else in the build depends on them. Remember to
bump `-Version` when you rebuild, or the console will keep showing the tiles of the package it already
has — and, worse, installing the *same* version twice unregisters the package.

## If you do make artwork

Keep it yours. Screenshots, logos, character art and fonts from the game belong to their owners, and a
package that carries them is a package you cannot share.
