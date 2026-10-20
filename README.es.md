# Bloody Roar II en Xbox — el port de UWP

Cómo coger la recompilación estática
[BloodyRoar2Recomp](https://github.com/novapowers0/BloodyRoar2Recomp) de *Bloody Roar II* (PlayStation,
1999, `SCUS-94424`) y hacerla correr **en una Xbox Series X en modo desarrollador**, como un paquete UWP
que compilas y firmas tú.

*(English: [README.md](README.md))*

No es una teoría: el juego arranca, se juega con mando en los menús y en la pelea, en 16:9 y con un
contador de FPS en pantalla que se conmuta con **R3**. Está jugándose en una consola de verdad desde el
2026-10-19.

## En qué consola se probó

**En una Xbox Series X**, en modo desarrollador. Y hay que leerlo tal cual:

- **Series X — probada.** Todo lo que se afirma aquí se midió en una.
- **Series S — nunca se probó.** Ni una vez. Este port dibuja cada cuadro en la **CPU** (en el App
  Container no hay OpenGL, así que el runtime se queda con su rasterizador por software), y la Series S
  tiene menos memoria y más lenta. Puede que corra, puede que corra más despacio, o puede que no
  sostenga ni un cuadro: nadie lo sabe, porque nadie lo ha intentado. Si la pruebas en una Series S, los
  FPS que te salgan no son los de más abajo.

## Qué es este repositorio

**Una receta y las herramientas que la aplican.** El proyecto del juego compila y corre muy bien en el
PC, pero su framework no traía **ni una sola línea** de UWP —ni una mención en `runtime.cmake`—, así que
todo lo que necesita una consola hubo que escribirlo: trece parches con ancla, un sustituto inerte del
backend de OpenGL, la entrada WinRT y los scripts de compilación y empaquetado. Todo esto se aplica
**a tu propia copia** del proyecto del juego, en tu máquina.

## Qué **no** es

Aquí no hay **código del juego, ni el C recompilado, ni imagen de disco, ni ejecutable, ni paquete
`.msix`, ni arte**. Esto no produce un juego jugable por sí solo, y nada de lo que se descargue de aquí
es un juego. Hacen falta tu propia copia legal del disco y el proyecto del juego compilando. Ver
[`NOTICE.es.md`](NOTICE.es.md).

Los mosaicos del paquete tampoco están: los de la consola de verdad se hicieron con arte del propio
juego, que es de Hudson Soft. Los pones tú — [`docs/ASSETS.es.md`](docs/ASSETS.es.md) tiene las medidas
exactas, y el script de empaquetado se detiene con un mensaje claro si la carpeta está vacía.

## Qué hace falta antes

| | |
|---|---|
| El proyecto del juego | [novapowers0/BloodyRoar2Recomp](https://github.com/novapowers0/BloodyRoar2Recomp), clonado con `--recurse-submodules` y **compilando y corriendo en tu PC primero** |
| Tu propio disco | Un volcado NTSC-U de `SCUS-94424` (`.bin` + `.cue`). **No hace falta BIOS retail**: el proyecto trae OpenBIOS, que es libre, y es la que va en el paquete |
| Visual Studio | 2022, con las herramientas de C++ **y el componente de C++ para UWP** (para `vcvarsall x64 uwp`, que es lo que enlaza contra el CRT del App Container) |
| El SDK de Windows | Para `makepri`, `makeappx` y `signtool`; el script de empaquetado busca el más nuevo que tengas |
| CMake y Ninja | El generador es **Ninja**: el de Visual Studio es multiconfiguración y este framework escribe un archivo de versión por configuración, que CMake rechaza |
| Python 3 | Para los parches. Nada más que la biblioteca estándar |
| Una Xbox Series X en modo desarrollador | Y un certificado con el que firmar; uno autofirmado vale ([`docs/INSTALL.es.md`](docs/INSTALL.es.md) §3) |

Un SDL2 2.30.2 compilado para `WindowsStore` es un requisito, no una descarga: SDL3 no tiene WinRT.
[`docs/INSTALL.es.md`](docs/INSTALL.es.md) §2 lo compila en dos órdenes.

## Cómo va

Tres órdenes. [`docs/INSTALL.es.md`](docs/INSTALL.es.md) es la versión larga de estas, con la parte de
la consola incluida.

> **Dónde se escribe esto:** en **PowerShell** —pulsa la tecla **Windows**, escribe `powershell` y pulsa
> **Enter**— en una ventana **normal**: no hace falta «ejecutar como administrador», y usarlo rompería el
> paso de la firma, porque el certificado vive en el almacén de quien ejecuta la orden. Desde la carpeta
> de este repositorio.

```powershell
# 1. parchear tu copia del proyecto del juego (idempotente, todo o nada, escritura atómica)
python tools\apply_uwp.py <raíz del proyecto del juego>

# 2. configurar y compilar para la consola
powershell -ExecutionPolicy Bypass -File tools\configurar-uwp.ps1 `
    -Raiz <raíz del proyecto> -Build <carpeta de compilación> -Sdl2 <carpeta cmake de SDL2> -Compilar

# 3. empaquetar y firmar (tus mosaicos, tu certificado)
powershell -ExecutionPolicy Bypass -File tools\empaquetar-uwp.ps1 `
    -Build <carpeta de compilación> -Salida <carpeta de salida> -Certificado <huella de tu certificado> -Version 1.0.0.0
```

`python tools\apply_uwp.py --list` imprime los trece pasos y qué resuelve cada uno.

Después, instalar el `.msix` por el Device Portal y subir tu disco **partido en trozos** a la carpeta de
datos de la aplicación. Paso a paso: **[`docs/INSTALL.es.md`](docs/INSTALL.es.md)**.

## Qué hubo que resolver

Cada una de estas fue un fallo real en la consola, y la mayoría tapaba a la siguiente. El detalle, con lo
que decía el registro en cada caso, está en
**[`docs/HOW-IT-WORKS.es.md`](docs/HOW-IT-WORKS.es.md)**.

| | Síntoma | Arreglo |
|---|---|---|
| 1 | No había compilación de UWP ninguna | El framework no tenía perfil de consola. Se le añade uno a `runtime.cmake`, encendido solo cuando `CMAKE_SYSTEM_NAME` es `WindowsStore` |
| 2 | El paquete se instalaba y la consola no lo lanzaba | `OPENGL32.dll`: basta con *importarla*. El backend de GL se sustituye por uno inerte y el runtime se queda con su rasterizador por software |
| 3 | `SDL_CreateWindow failed: Could not initialize OpenGL` | El runtime detecta que GL no está, pero después de pedirle a SDL una ventana con contexto GL. Ahora el dibujo por software se elige *antes* de crear la ventana |
| 4 | Errores de enlazado en App Container | `MessageBoxA`, `GetOpenFileNameA`, `SetErrorMode`, DbgHelp, `CreateProcess`, `TerminateJobObject`, `CreateFiber`: ninguna existe allí. Cada una se guarda o se desvía al camino que el framework ya tiene para los demás sistemas |
| 5 | `C atomic support is not enabled` | El framework pasa `/experimental:c11atomics` al único archivo que conocía; hay un segundo que también lo necesita |
| 6 | `fatal error RC1107: invalid usage` | El compilador de recursos se atraganta con los `-D` del proyecto. En UWP el icono lo dan los Assets del paquete de todas formas |
| 7 | `LNK2019` en `SDL_main` | Con el juego en red apagado, el registro del lobby se sigue llamando, y sin guarda: es un fallo del framework, no de UWP |
| 8 | `LNK2019` pidiendo `main(Platform::Array<String^>^)` | Una aplicación UWP no arranca por `main()`. La entrada WinRT de SDL, compilada con `/ZW` |
| 9 | `-DPSX_SETUP_WIZARD=OFF` no surtía efecto | El CMake del juego lo fija con `FORCE`, que pisa la línea de órdenes |
| 10 | No se podía escribir nada: partidas, registros, configuración | El runtime ancla cada archivo junto al ejecutable, que en UWP es la carpeta de instalación, de solo lectura. Ahora ancla en la carpeta de datos |
| 11 | `savestate: SAVE FAILED … \WindowsApps\…` | Un camino distinto y aparte: `memcard_dir` era relativa y se resolvía contra la carpeta de solo lectura |
| 12 | El mando no hacía nada | Sin lanzador que asigne dispositivo, el jugador 1 se queda en **teclado**, y sin un solo aviso. Las dos ranuras pasan a `auto` |
| 13 | No había forma de ver los FPS | Una consola no tiene rótulo de ventana, que es donde el runtime los escribe, y la capa de pantalla solo se compilaba con el lanzador. Contador en pantalla, **R3** lo conmuta |
| 14 | `cannot launch with selected mods: package does not target this game/image` | Los mods —y con ellos la huella de disco que cada uno exige— se validan *antes* de resolver el disco. Aquí es fatal, porque el panorámico va encendido y su manifiesto lleva el SHA-256 del disco |
| 15 | El disco no subía: HTTP 500 | Las subidas del portal pasan por `D:\DevelopmentFiles`, que es pequeña y suele estar casi llena. El disco sube en partes de 150 MiB y la entrada WinRT las une en el primer arranque |

## Qué no está resuelto

Dos cosas, dichas claramente porque descubrirlas por las malas es peor:

- **No sostiene 60 FPS en todas partes.** 60 casi siempre, pero baja a **55 y hasta 50** en algunos
  escenarios y peleas; el registro da **52-54 fps** en la demostración de atracción del propio juego, que
  es la escena más cargada, y **59,0** en pantallas ligeras. Son dos cosas distintas, y
  [`docs/HOW-IT-WORKS.es.md`](docs/HOW-IT-WORKS.es.md) §7 tiene las medidas: un 0,98x fijo que es el
  marcapasos por reloj de pared, no falta de potencia, y las bajadas de verdad, que son el rasterizador
  por software quedándose sin tiempo. ⚠ Forzar la cadencia a 60 Hz para que mandara la sincronía del
  driver **empeora** —48,0 fps en la misma ventana de medida— porque el cuadro que se pasa de 16,67 ms
  pierde el refresco entero. Se probó, se midió y se revirtió.
- **No vuelve donde lo dejaste.** En modo desarrollador la Xbox *termina* un juego que pasa a segundo
  plano, así que al volver de Home arranca de cero. La maquinaria de estados del framework está y
  funciona; atarla al estado de activación no está hecho en este port.

Las dos están abiertas como issues de este repositorio.

## Cómo se verificó la receta

Lo que hace creíble a este repositorio no es que compile, sino que **aplicado a un clon limpio deja el
árbol del que salió el paquete que corre en la consola**:

- clon limpio del proyecto del juego en el commit del que salió el paquete, con el submódulo del
  framework en su ancla;
- `apply_uwp.py` entero, dos veces (la segunda no cambia nada: cada paso es idempotente);
- los diez archivos que toca, comparados con el árbol de referencia: **uno idéntico byte a byte**, ocho
  idénticos salvo los comentarios y `runtime.cmake` idéntico salvo tres mensajes de CMake. Los
  comentarios y los mensajes van aquí en inglés, como el resto del runtime, y es el único cambio hecho a
  propósito; en el árbol de referencia estaban en castellano.
- el sustituto inerte de GL pasa `clang -fsyntax-only -Wall -Wextra` sin un aviso.

Las cifras y lo que **no** se volvió a medir están en
[`docs/HOW-IT-WORKS.es.md`](docs/HOW-IT-WORKS.es.md).

## Créditos y licencia

Port y herramientas de **Recompilaciones**. Publicado bajo la
[PolyForm Noncommercial License 1.0.0](LICENSE), la misma del framework psxrecomp del que esto es un
derivado.

Los scripts de los parches llevan sus comentarios en castellano, que es donde se escribieron; lo que
escriben *dentro* del árbol del juego va en inglés, como el resto del runtime. La documentación está en
los dos idiomas.

*Bloody Roar II* es © Hudson Soft / Eighting. Este proyecto no está afiliado con ellos, ni con Konami, ni
con Sony, ni con Microsoft, ni con los autores del proyecto del juego o del framework, y no distribuye
nada que les pertenezca. El detalle —qué hay y qué no hay aquí exactamente, cuánto se cita de trabajo
ajeno y cómo pedir una retirada— está en [`NOTICE.es.md`](NOTICE.es.md). Los titulares de derechos
pueden escribir a **jajdpmail@gmail.com**.
