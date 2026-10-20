# Los mosaicos del paquete

*(English: [ASSETS.md](ASSETS.md))*

Un paquete UWP necesita sus mosaicos. **Este repositorio no trae ninguno**: los de la consola de verdad
se recortaron del arte del propio juego, que es de Hudson Soft, y eso es justo lo que
[`NOTICE.es.md`](../NOTICE.es.md) promete no distribuir. Los pones tú.

`tools/empaquetar-uwp.ps1` lee `package/Package.appxmanifest`, averigua qué PNG nombra y se detiene antes
de hacer nada si falta alguno, diciéndote cuál.

## Qué poner en `package/Assets/`

Los cuatro que nombra el manifiesto, que son los que la compilación exige de verdad:

| Archivo | Medidas |
|---|---|
| `SplashScreen.png` | 620 × 300 |
| `Square150x150Logo.png` | 150 × 150 |
| `Square44x44Logo.png` | 44 × 44 |
| `StoreLogo.png` | 50 × 50 |

Y las variantes escaladas que lleva un paquete completo. Para la compilación son opcionales, pero sin
ellas la consola agranda las de base:

| Archivo | Medidas |
|---|---|
| `SplashScreen.scale-200.png` | 1240 × 600 |
| `Square150x150Logo.scale-200.png` | 300 × 300 |
| `Square44x44Logo.scale-200.png` | 88 × 88 |
| `Square44x44Logo.targetsize-24_altform-unplated.png` | 24 × 24 |
| `StoreLogo.scale-200.png` | 100 × 100 |
| `LockScreenLogo.png` | 24 × 24 |
| `LockScreenLogo.scale-200.png` | 48 × 48 |

PNG de 32 bits con alfa. Las medidas no son una recomendación: un mosaico del tamaño equivocado hace que
`makepri` produzca un índice de recursos que la consola no acepta.

`Wide310x150Logo.png` (310 × 150) es **opcional y está comentado** en el manifiesto: la consola no lo usa
en modo desarrollador, y referenciar un PNG que no existe hace fallar a `makepri` y a `makeappx`. Si lo
quieres, añade el archivo y descomenta la línea de `uap:DefaultTile`.

## La forma más rápida de tener algo que funcione

Cualquier imagen con esas medidas exactas vale: la consola solo necesita que existan y que tengan la
forma correcta. Con ImageMagick, si lo tienes, las once salen de una vez.

> **Dónde se escribe esto:** en **PowerShell** —pulsa la tecla **Windows**, escribe `powershell` y pulsa
> **Enter**— en una ventana **normal**: no hace falta «ejecutar como administrador». Desde la carpeta de
> este repositorio.

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

Cámbialos por arte de verdad cuando quieras: nada más en la compilación depende de ellos. Acuérdate de
subir `-Version` al rehacer el paquete, o la consola seguirá mostrando los mosaicos del que ya tiene —y,
peor, instalar **la misma** versión dos veces desregistra el paquete.

## Si haces arte

Que sea tuyo. Las capturas, los logotipos, el arte de los personajes y las tipografías del juego son de
sus propietarios, y un paquete que los lleve dentro es un paquete que no puedes compartir.
