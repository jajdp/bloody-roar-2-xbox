# Cómo funciona, y lo que costó

*(English: [HOW-IT-WORKS.md](HOW-IT-WORKS.md))*

Trece parches, un archivo de sustitución y una entrada WinRT. Esto es para qué sirve cada uno, qué decía
la consola antes de él y qué se midió. El orden de aquí es el que aplica
[`../tools/apply_uwp.py`](../tools/apply_uwp.py), y ese orden está verificado, no supuesto: ver §10.

Todo lo que se mide aquí se midió en una **Xbox Series X** en modo desarrollador. Nunca se ha ejecutado
nada en una Series S.

## 0. El punto de partida: un framework sin consola dentro

El proyecto del juego compila y se juega en Windows. Su framework —`psxrecomp`, en el ancla que el
proyecto fija— no tenía **ni una mención de UWP** en `runtime.cmake`. Para comparar: el port hermano de
otro juego de psxrecomp encontró 28 menciones en su propio fork del framework, porque el autor de ese
fork había empezado el trabajo. Aquí no había nada: ni perfil, ni guardas, ni sustituto para las partes
de Windows que un App Container no tiene.

Así que el primer parche no es un arreglo, es un perfil. `parche_uwp.py` añade a `runtime.cmake`:

- `PSX_UWP`, encendido solo cuando `CMAKE_SYSTEM_NAME` es `WindowsStore`;
- sin servidor de depuración (su socket TCP no está permitido), sin lanzador y sin Vulkan;
- SDL2 por paquete de CMake, porque SDL3 no tiene backend de WinRT;
- `PSX_UWP=1` para el compilador, que es de lo que cuelgan todas las guardas de abajo;
- `/APPCONTAINER` en el enlazado y `SDL_MAIN_HANDLED` apagado, que es lo que permite que la entrada
  WinRT sea la entrada.

Sus cuatro anclas sobrevivieron a **583 líneas de cambios** en ese solo archivo entre la revisión del
framework que usó el port hermano y la que fija este juego. Ese es el argumento de las anclas frente a
los números de línea.

## 1. «Failed to launch the application»

El paquete se instalaba, aparecía en la lista y no hacía nada al lanzarlo. Sin registro, sin ventana y
sin más error que esa línea del portal. Había dos causas, y la primera tapaba a la segunda.

**El CRT del App Container.** Compilado con `vcvars64`, el ejecutable importa `msvcp140.dll` y
`kernel32.dll`, el CRT de escritorio. Una consola tiene las variantes `_app`, por el paquete de marco de
VCLibs. `vcvarsall x64 **uwp**` es lo que pone `lib\x64\store` en `LIB`, y por eso el §5 de
[`INSTALL.es.md`](INSTALL.es.md) insiste tanto.

**`OPENGL32.dll`.** Esta conviene decirla claramente, porque es invisible: *basta con importar* una DLL
que la consola no tiene para que el sistema se niegue a activar la aplicación. El backend de GL del
runtime llama a GL 1.x directamente, así que la importación estaba ahí. El arreglo es
[`../src/gpu_gl_renderer_stub.c`](../src/gpu_gl_renderer_stub.c), una unidad de traducción de reemplazo
que define los mismos símbolos, todos inertes, para que el resto enlace igual y el runtime se quede con
su rasterizador por software, que es el que usa en una consola de todas formas. `dbghelp` y `comdlg32`
se fueron por el mismo camino: en UWP no hay que enlazar nada por nombre, porque `WindowsApp.lib` es la
biblioteca paraguas que CMake añade para `WindowsStore` y ya trae lo permitido, los sockets incluidos.

El sustituto pasa `clang -fsyntax-only -Wall -Wextra` sin un aviso. Tiene una función que el del port
hermano no necesitaba: `gl_renderer_set_scanlines`, que el camino de presentación de este framework
llama.

## 2. `SDL_CreateWindow failed: Could not initialize OpenGL / GLES library`

Sin GL, el arranque siguiente llegó más lejos y murió aquí. El runtime *sí* detecta que GL no está y lo
dice —`renderer = opengl requested but unavailable — falling back to software`—, pero eso ocurre
**después** de crear la ventana, y la preferencia que lee al crearla seguía diciendo `opengl`, así que a
SDL se le pedía una ventana con contexto GL. `parche_uwp_render_software.py` fija el renderizador por
software en el perfil UWP, antes de elegir el backend.

## 3. Todo lo que el App Container no tiene

Cinco fallos distintos de enlazado o de compilación, cada uno encontrado al arreglar el anterior. Están
todos en `parche_uwp_codigo.py` y `parche_uwp_codigo_br2.py`:

| Qué | Por qué no está | Qué hace el parche |
|---|---|---|
| `MessageBoxA` | No hay cuadros de diálogo en un App Container | Los dos avisos van solo al registro |
| `GetOpenFileNameA` / `OPENFILENAMEA` | Lo mismo, y en un televisor no habría dónde abrir un selector de archivos | Se guarda |
| `SetErrorMode` + `SEM_*` | No se exportan | Se guarda; solo servía para suprimir un cuadro de error de Windows que allí no existe |
| DbgHelp (`SymInitialize`, `StackWalk64`, `SymFromAddr`) | No está, y caminar la pila de otro hilo no se permite | El volcado de la pila del hilo principal devuelve `[]`. El latido sigue escribiendo todo lo demás, igual que en un PC donde no se resuelven los símbolos |
| `CreateProcess`, herencia de descriptores, `TerminateJobObject` | No están | La recompilación al vuelo cae en la rama que el framework ya tiene para los demás sistemas: `manual compile flow only`. En una consola no hay compilador que lanzar |
| `CreateFiber` / `ConvertThreadToFiber` | Solo se exportan las variantes `…Ex` | Una rama para la consola, elegida por `WINAPI_FAMILY`, con `CreateFiberEx` y `ConvertThreadToFiberEx`. Las fibras son el motor del planificador del BIOS, así que esto no es opcional |

Y dos que **no** son culpa de UWP:

- **`C atomic support is not enabled`.** El framework pasa `/experimental:c11atomics` «scoped to the one
  C source that needs it». Hay un segundo archivo que también lo necesita —el guardia de inanición— y
  MSVC corta. Son los dos únicos `.c` del runtime que incluyen `<stdatomic.h>`.
- **`LNK2019` en `SDL_main`.** Con el juego en red apagado, el cliente del lobby no se compila, pero el
  runtime sigue llamando a su función de registro, y sin guarda. Es un fallo del framework que solo
  aparece en una compilación sin juego en red; el parche guarda la llamada.

## 4. `fatal error RC1107: invalid usage`

El compilador de recursos, invocado para el icono del ejecutable, se atraganta porque CMake le pasa los
`-D` del proyecto y el título de la ventana lleva espacios y paréntesis. En UWP el icono lo dan los
Assets del paquete, así que la rama de Windows se deja fuera del perfil de la consola; el PNG se sigue
copiando al lado del ejecutable, como antes.

## 5. No se podía escribir nada, y de dos maneras distintas

El runtime ancla **todos** sus archivos —configuración, disco, BIOS, tarjetas de memoria, cachés,
registros— en el directorio del ejecutable, y lo dice en su propio comentario: *«Deliberately NEVER the
current working directory»*. En UWP ese directorio es la carpeta de instalación del paquete, que es de
solo lectura.

`parche_uwp_rutas.py` hace que esa función devuelva la carpeta de datos de la aplicación al compilar
para la consola, que es donde el Device Portal puede dejar cosas y donde se puede escribir. La deduce
del Temp del propio paquete (`…\AC\Temp`, dos niveles arriba) para que nada tenga que inicializar la
Windows Runtime antes que SDL.

No bastó, y la segunda mitad es de las cosas que solo encuentra una ejecución de verdad. El registro
decía:

```text
savestate: SAVE FAILED slot 99 -> S:\Program Files\WindowsApps\<paquete>\saves/scph1001/state_….pst
```

El `game_us.toml` se carga de la carpeta de instalación, y su `[runtime] memcard_dir = "saves"` es una
ruta **relativa**, que se resuelve contra la carpeta de ese mismo archivo. Así que las tarjetas de
memoria y los estados apuntaban a un sitio de solo lectura: una ruta que ya venía resuelta antes de que
el parche del ancla pudiera hacer nada al respecto. `parche_uwp_escritura.py` la vuelve a anclar en la
carpeta de datos en cuanto queda resuelta.

## 6. El mando no hacía nada, y sin avisar

El juego llegaba al título y el mando no respondía. Tampoco había nada en el registro, que es lo que lo
hizo lento: el runtime asigna el dispositivo de cada jugador por `[controller] device`, y sin ajustes el
reparto de fábrica en una compilación de producto es **teclado** para el jugador 1, porque en un PC lo
normal es que el lanzador escriba el dispositivo elegido antes de arrancar. En una consola no hay
lanzador ni teclado, y el mensaje que te lo habría dicho (`opened controller for slot`) solo se imprime
para los jugadores cuyo tipo es mando.

`parche_uwp_mando.py` deja las dos ranuras en `auto` —el primer mando conectado— al compilar para la
consola, y [`../config/settings.toml`](../config/settings.toml) trae los mismos valores de fábrica, en
modo digital, que es como se juega este juego.

## 7. Los FPS: qué se sabe, qué se midió y qué sigue abierto

Una consola no tiene rótulo de ventana, que es justo donde el runtime escribe los FPS. Y la capa de
pantalla que podría mostrarlos —`host_osd.c`, con su propia fuente de 8×8— estaba detrás de
`#if defined(RECOMP_LAUNCHER)`, así que solo se compilaba cuando el producto llevaba el lanzador. Dos
parches: `parche_uwp_osd.py` compila esa capa también para el perfil UWP (no necesita nada de
recomp-ui) y `parche_uwp_fps_encendido.py` enciende el contador de fábrica, porque los interruptores
que el framework trae para eso son una variable de entorno y un atajo de teclado, y una consola no tiene
ninguno de los dos.

`parche_uwp_fps_r3.py` ata **R3** —pulsar el stick derecho— a conmutarlo. Ese botón es seguro: el mando
va en modo digital, donde los clics de los sticks del DualShock no existen, así que el juego nunca lo ve.

⚠ **Dónde va la comprobación es la trampa**, y se pagó dos veces: en el bucle de eventos de SDL no
funciona (ese bucle es el bombeo que mantiene viva la ventana, y el evento del botón no llega ahí), y
dentro de la función que arma la palabra del mando para el juego tampoco (no se recorre en cada cuadro).
Va sobre la palabra del mando, antes del SIO, que sí.

### Lo que enseñó el contador

| Escena | Medido | Proporción |
|---|---|---|
| Pantallas ligeras (menús, cargas) | **59,0 fps** | 0,98x |
| La demostración de atracción del propio juego, la escena más cargada | **52-54 fps** | 0,88-0,90x |
| Jugando | 60 casi siempre, bajando a **55 y hasta 50** en algunos escenarios y peleas | — |

**Son dos problemas distintos, y solo uno es de potencia.**

- El **0,98x fijo** es el marcapasos. SDL/WinRT no le dice al runtime la frecuencia del panel —el
  registro dice `host refresh unknown`—, así que marca los cuadros por reloj de pared, y eso se desvía
  un 2% más o menos. No es falta de rendimiento.
- Las **bajadas a 50-56** sí son reales: el rasterizador por software no termina el cuadro a tiempo en
  las escenas más cargadas.

⚠ **Se probó un arreglo, se midió y se revirtió.** Forzar la cadencia a 60 Hz para que mandara la
sincronía del driver dio **48,0 fps (0,80x)** en la misma ventana de medida, frente a los 52-54 del
marcapasos por reloj. La razón es simple cuando se ve: el cuadro que se pasa del presupuesto de 16,67 ms
pierde el refresco *entero*, así que el castigo va a saltos. Está en este documento y no en el
repositorio porque saber lo que no funciona vale tanto como la receta.

El camino es **abaratar el dibujo** —medir dónde se va el tiempo, caminos rápidos del rasterizador,
quitar trabajo del camino caliente—, que es lo que hizo un port hermano de esta familia para llegar a 60
sostenidos. Ese trabajo no está hecho aquí, y está abierto como issue.

## 8. Los mods, el disco y el orden en que pasan las cosas

El framework valida los paquetes de mods —y con ellos la huella de disco que cada uno exige— **antes**
de resolver dónde está el disco de verdad: `mod_runtime_commit(resolved_disc)` ocurre antes de que
`resolved_disc` tenga la ruta real. En un PC es inofensivo, porque a esas alturas trae la que el
`game_us.toml` del proyecto lleva escrita. En una consola esa ruta no puede existir: el disco vive en la
carpeta de datos del paquete y su ruta depende de la instalación, así que el empaquetado quita la clave.

El resultado fue que el sistema de mods calculaba la huella de un disco vacío y se negaba a arrancar:

```text
psxrecomp: cannot launch with selected mods: package does not target this game/image: br2.enhancement.widescreen
```

Y aquí eso es fatal, no molesto, porque el panorámico va **encendido** —en una consola no hay pestaña
Mods donde marcarlo— y su manifiesto lleva el SHA-256 del disco de las tres regiones.
`parche_uwp_disco_mods.py` resuelve el disco desde el puntero `disc.cfg` justo antes de la comprobación.

⚠ **Su ancla no es la del port hermano.** Entre las dos revisiones del framework el bloque del juego en
red se reescribió entero, y el ancla heredada daba *cero* apariciones. La llamada sigue en el mismo
sitio, pero ahora cuelga de un if-else con el plan de netplay del lanzador. Este es el tipo de fallo de
parche más útil: se detuvo, dijo el archivo y el recuento, y no escribió nada.

## 9. El disco no va dentro del paquete

Las subidas del portal pasan por `D:\DevelopmentFiles`, una partición de unos 5 GB que suele estar casi
llena, y una subida de 527 MiB responde HTTP 500. `tools/partir_disco.py` corta el `.bin` en partes de
150 MiB —cuatro para este juego— y la entrada WinRT las une en el siguiente arranque, una sola vez,
anotando `partes: 4 unidas, 552729408 bytes`. Ese número es el tamaño exacto del volcado, que es para lo
que se imprime.

La entrada, [`../src/SDL_winrt_main_NonXAML.cpp`](../src/SDL_winrt_main_NonXAML.cpp), es la de SDL
(dominio público, David Ludwig) con eso y algunas cosas más añadidas en su sitio: sembrar la carpeta de
datos desde el paquete en cada arranque, escribir `bios.cfg` y `disc.cfg` con rutas absolutas, desviar la
salida del runtime a registros que el portal pueda leer, anotar cómo se activó la aplicación y pedirle a
SDL que atienda el botón **B** para que el sistema no lo tome como «atrás» y cierre el juego.

⚠ **Dentro había tres valores de otro juego**, heredados del port hermano, y los tres fallan en silencio
en vez de a gritos. Se listan aquí porque quien lleve esta receta a un *tercer* juego se va a encontrar
exactamente los mismos tres: el **serial** en la entrada (crea la carpeta de datos con el nombre
equivocado), la **subcarpeta de datos** en el parche de rutas (el runtime busca sus archivos donde no
están) y la **lista de siembra** de la entrada (este juego tiene una configuración por región, así que
`game_us.toml` tiene que estar en esa lista o su configuración no se siembra nunca).

## 10. Cómo se verificó la receta

Lo que se afirma no es «compila». Lo que se afirma es que **esta receta produce el árbol del que salió el
paquete probado**, y se comprobó así:

1. Un clon limpio del proyecto del juego en `eed1e8d1`, con el submódulo del framework en `219a3627`.
2. La cadena aplicada sobre él: primero con los scripts del propio proyecto, para establecer cuál es el
   árbol de referencia; después, sobre otro clon limpio, con los scripts publicados de este repositorio.
3. Los **diez archivos que toca la cadena**, comparados byte a byte:
   - contra el árbol de referencia, la cadena del proyecto da **9 de 10 idénticos**. El décimo es
     `main.cpp`, que difiere en exactamente **3 bytes**: un BOM de UTF-8 que el árbol de desarrollo había
     recogido por el camino.
   - contra ese resultado, la cadena de este repositorio da **uno idéntico byte a byte**, **ocho
     idénticos salvo los comentarios** y `runtime.cmake` idéntico salvo **tres mensajes de CMake**. Los
     comentarios y los mensajes van aquí en inglés, como el resto del runtime, y es el único cambio hecho
     a propósito. Los parches publicados tampoco añaden ya ese BOM a los cinco archivos del framework que
     lo habían ganado.
4. El `git status` de los dos clones lista *las mismas diez rutas* y nada más, así que la receta no toca
   nada que no declare.
5. La cadena entera pasada **dos veces**: la segunda no escribe nada y lo dice. Cada parche es
   idempotente, todo o nada y atómico (un `.tmp` al lado del archivo y un reemplazo de una vez).
6. `clang -fsyntax-only -Wall -Wextra` sobre el sustituto de GL: ni un aviso.

### Qué no se volvió a medir, y por qué

- **La compilación de UWP y el paquete.** Rehacerlos necesita los 68 MB de C generados desde un disco y
  el entorno de UWP; lo que se publica es la receta, y el binario que salió de ella es el que está
  jugándose en una consola desde el 2026-10-19.
- **Nada en una Series S.** Nunca se ha intentado. Ver el README.
- **El arreglo de los 60 FPS**, porque todavía no hay uno (§7).
