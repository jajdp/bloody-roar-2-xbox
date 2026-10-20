# Aviso

*(English: [NOTICE.md](NOTICE.md))*

## Sin afiliación

Esto es un proyecto de aficionado, no oficial y sin ánimo de lucro. **No está afiliado, respaldado ni
conectado con Hudson Soft, Eighting, Konami, Sony ni Microsoft**, ni con ninguna de sus filiales, ni con
el autor del framework [psxrecomp](https://github.com/RetroPortingToolKit/psxrecomp), ni con el autor del
[proyecto del juego](https://github.com/novapowers0/BloodyRoar2Recomp) sobre el que está hecho este port.
*Bloody Roar*, *Xbox* y todos los nombres y marcas relacionados son de sus respectivos propietarios, y
aquí se usan solo para decir con qué funciona esto.

Nada de esto está en venta, y nada de esto está monetizado.

## Qué NO distribuye este repositorio

Ningún código del juego. Ninguna imagen de disco. **Ningún C recompilado**: los 56 archivos y 68 MB de C
que hacen funcionar este juego los genera el recompilador del propio proyecto desde *tu* disco, en tu
máquina; son código del juego y nunca salen de aquí. Ningún ejecutable compilado. Ningún paquete `.msix`.
Ninguna partida guardada. Ningún arte, audio, música ni tipografía del juego, **ni los mosaicos del
paquete**: por eso `package/Assets/` está vacía y [`docs/ASSETS.es.md`](docs/ASSETS.es.md) te pide que
pongas los tuyos.

Tampoco ninguna BIOS, y no hace falta: el proyecto del juego trae OpenBIOS, que es software libre, y es
la que lleva el paquete.

Nada de aquí produce un juego jugable por sí solo. Hacen falta tu propia copia legal del disco y el
proyecto del juego compilando, y este repositorio no da ni puede dar ninguna de las dos cosas.

## Qué contiene de trabajo ajeno

Medido, archivo por archivo, contra los dos árboles originales en las revisiones de las que salió este
port: **77 líneas en 33 anclas**. Un ancla es el texto que un parche comprueba antes de escribir, para
que falle del lado seguro en vez de estropear un árbol que no reconoce.

| De quién | Líneas | Anclas | Dónde |
|---|---|---|---|
| El framework psxrecomp | **70** | 31 | `runtime.cmake` (16), `main.cpp` (37), `host_osd.c` (5), `autocompile.c` (5), `freeze_heartbeat.c` (4), `psx_fiber.c` (2), `crash_trace.c` (1) |
| [novapowers0/BloodyRoar2Recomp](https://github.com/novapowers0/BloodyRoar2Recomp) | **7** | 2 | `CMakeLists.txt`, en `tools/parche_uwp_cmake_juego.py` |

**El framework** que usa el juego es
[novapowers0/psxrecomp](https://github.com/novapowers0/psxrecomp) (rama `nova-mods`), un fork de
[RetroPortingToolKit/psxrecomp](https://github.com/RetroPortingToolKit/psxrecomp). Lleva la **PolyForm
Noncommercial License 1.0.0**, © 2026 Matthew Stan, que permite obras derivadas no comerciales. Este
repositorio es una de esas obras y se publica bajo [esa misma licencia](LICENSE): el texto canónico de
[polyformproject.org](https://polyformproject.org/licenses/noncommercial/1.0.0), con su
`Required Notice`.

**El proyecto del juego** lleva la **licencia MIT**, © 2026 BloodyRoar2Recomp contributors, y es por eso
que sus siete líneas de `CMakeLists.txt` se pueden citar. La MIT pide que su aviso viaje con las partes
sustanciales del software; siete líneas de script de compilación dentro del ancla de un parche no son
eso, y aquí no se reproduce ningún archivo de ese proyecto, pero se lo nombra y se lo enlaza donde se lo
cita, y este es el aviso.

**`src/SDL_winrt_main_NonXAML.cpp`** es la entrada WinRT de SDL, *puesta en dominio público por David
Ludwig*, con lo que este port necesitaba marcado dentro: sembrar la carpeta de datos escribible de la
aplicación, unir el disco subido en partes, escribir los punteros `bios.cfg` / `disc.cfg`, desviar la
salida del runtime a un registro que el Device Portal pueda leer, anotar por qué se activó la aplicación
y evitar que **B** cierre el juego. El original es parte de [SDL](https://github.com/libsdl-org/SDL).

**`src/gpu_gl_renderer_stub.c`** es nuestro. Define los mismos símbolos que el backend de OpenGL del
framework, todos inertes, para que el resto del runtime enlace igual mientras GL no está disponible; los
nombres y las firmas vienen de la cabecera pública del propio framework, que es a lo que tiene que
ajustarse cualquier sustituto de una interfaz.

**Aquí no hay ni una captura de pantalla.** Una captura de esto funcionando sería casi toda arte de
Hudson Soft, y estaría mostrando su trabajo en vez del de aquí.

## Retirada y contacto

Si tienes derechos sobre este material y quieres que algo de aquí se quite o se cambie, escribe a
**jajdpmail@gmail.com**, diciendo a qué te opones y en calidad de qué escribes.

Las peticiones de los titulares de derechos se atienden: se quita la parte en disputa, o se retira el
repositorio, sin discusión, y recibirás una respuesta confirmándolo. No hace falta ningún aviso ni
proceso legal más allá de ese correo para llegar a la persona que mantiene esto.
