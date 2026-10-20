# Compilar el port y meterlo en la consola

*(English: [INSTALL.md](INSTALL.md))*

Nueve pasos. Los pasos 1 a 3 se hacen una sola vez; del 4 en adelante, rehacer el paquete son dos
órdenes.

Todo esto se hizo en una **Xbox Series X** en modo desarrollador. Una Series S no se ha probado nunca
—ver el README—. La parte del PC es la misma en cualquier caso.

## 0. Antes de empezar: dónde se escriben las órdenes

Esta guía está llena de bloques como este. **Son todas órdenes que escribes tú** en una ventana de
terminal, y cada una dice encima desde dónde. Si nunca has usado una, esta sección es todo lo que hace
falta; si sí, sáltala.

### La terminal: PowerShell

Todo lo de esta guía va en **PowerShell**, la terminal normal de Windows:

1. Pulsa la tecla **Windows**.
2. Escribe `powershell`.
3. Pulsa **Enter** en *Windows PowerShell*.

Se abre una ventana con una línea que termina en `>`. Ahí se escribe la orden y se pulsa **Enter**.

**Moverse a una carpeta.** Casi todas las órdenes se escriben *desde una carpeta concreta*, normalmente
la de este repositorio. Se llega con `cd` y la ruta, entre comillas si tiene espacios:

```powershell
cd "C:\Users\tu-nombre\Downloads\bloody-roar-2-xbox"
```

**Un atajo que ahorra errores:** abre la carpeta en el Explorador, haz clic en la barra de direcciones,
escribe `powershell` encima de lo que haya y pulsa **Enter**. PowerShell se abre ya en esa carpeta.

⚠ Algunas órdenes son largas y van partidas en varias líneas con un **acento grave** (`` ` ``) al final
de cada una. Cópialas enteras, con los acentos graves incluidos: son lo que dice «sigue en la línea
siguiente».

### No hace falta administrador, y es mejor que no

Nada de esta guía necesita «ejecutar como administrador». Todo se compiló y se probó desde una cuenta
normal.

> ⚠ Y en un paso, ser administrador lo **rompe** de verdad: el certificado del §3 se crea en el almacén
> del usuario que ejecuta la orden. Creado con elevación, acaba en el almacén del administrador, así que
> al empaquetar —como tú— `signtool` no lo encuentra y falla sin decir por qué.
>
> Lo único que pide permisos de administrador es el **instalador** de Visual Studio, y los pide solo.

### Cómo saber si una orden funcionó

Las de aquí terminan diciendo qué hicieron, y también lo dicen cuando algo va mal. Una orden que no
imprime nada normalmente ha funcionado; para asegurarse, esto responde `True` cuando la anterior salió
bien:

```powershell
$?
```

---

## 1. Qué hace falta antes

| | |
|---|---|
| **El proyecto del juego, ya funcionando en tu PC** | [novapowers0/BloodyRoar2Recomp](https://github.com/novapowers0/BloodyRoar2Recomp), clonado con `--recurse-submodules`. Compílalo y juégalo en Windows primero. Si no corre ahí, no va a correr en una consola, y estarías depurando dos cosas a la vez |
| **Tu propio disco** | Un volcado NTSC-U de `SCUS-94424` (`.cue` + `.bin`, unos 527 MiB) |
| **Ninguna BIOS retail** | A diferencia de otros títulos de psxrecomp, este arranca con la **OpenBIOS** que trae el proyecto, que es software libre y es la que va dentro del paquete. Si prefieres tu BIOS retail, el §9 dice dónde va |
| **Visual Studio** | «Desarrollo para el escritorio con C++», más el SDK de Windows 10/11 y Ninja. La versión no está fijada: `configurar-uwp.ps1` lo busca con `vswhere -latest`. Lo que de verdad necesita son tres cosas: que `vcvarsall.bat` acepte el argumento **`uwp`**, que esté el **CRT del App Container** en `VC\Tools\MSVC\<versión>\lib\x64\store\`, y que **`cl.exe /ZW`** compile, porque la entrada WinRT es C++/CX |
| **Un SDL2 compilado para WindowsStore** | Paso 2 |
| **Una Xbox en modo desarrollador** | Registrada y con el Device Portal accesible desde tu PC |
| **PowerShell** | La que trae Windows (Windows PowerShell 5.1) basta: **no hace falta PowerShell 7** |

Este port se desarrolló contra el commit `eed1e8d1` del proyecto del juego, con el submódulo
`psxrecomp` en `219a3627` y `recomp-ui` en `b688ca79`, que son las anclas que el propio proyecto anota en
`framework_pins.txt`. Un framework mucho más nuevo puede haber movido el código en el que se anclan los
parches; **cada parche comprueba su ancla y se detiene en vez de estropear nada**, así que lo sabrás al
instante y por su nombre.

> ⚠ **Un Visual Studio más nuevo no es automáticamente mejor aquí.** Microsoft lleva años retirando UWP,
> y este port se apoya en dos cosas que ya ha marcado como obsoletas en otros sitios: el objetivo `uwp`
> de `vcvarsall` y las extensiones C++/CX. Si alguna versión quita cualquiera de las dos, esta receta no
> funcionará en ella por nueva que sea.

### El C recompilado sale de tu disco, y va primero

Los 56 archivos y 68 MB de C que *son* este juego los genera el recompilador del propio proyecto, desde
tu disco, en tu máquina. Eso pasa en el flujo normal del proyecto en el PC, que es por lo que el paso 1
te pide tenerlo funcionando allí primero, y tiene que estar hecho **antes** de compilar para la consola,
porque el recompilador es un programa de escritorio y no corre dentro del entorno de UWP.

Si tu árbol tiene una carpeta `generated/` con los archivos C de `SCUS_944.24`, estás listo.

---

## 2. Un SDL2 para WindowsStore

**SDL3 no tiene backend de WinRT**, así que el port usa el de SDL2. Hace falta un SDL2 compilado para
`WindowsStore`; el 2.30.2 es el que se probó.

> **Dónde se escribe esto:** en **PowerShell** —pulsa la tecla **Windows**, escribe `powershell` y pulsa
> **Enter**— en una ventana **normal**: no hace falta «ejecutar como administrador». Desde donde hayas
> descomprimido las fuentes de SDL2.

```powershell
cmake -S <fuentes-sdl2> -B <compilacion-sdl2> -G Ninja `
      -DCMAKE_SYSTEM_NAME=WindowsStore -DCMAKE_SYSTEM_VERSION=10.0 `
      -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=<instalacion-sdl2>
cmake --build <compilacion-sdl2> --target install
```

Lo que se le pasa después a `-Sdl2` es la carpeta que tiene dentro `SDL2Config.cmake`, normalmente
`<instalacion-sdl2>/cmake` o `<instalacion-sdl2>/lib/cmake/SDL2`.

---

## 3. Un certificado con el que firmar

El modo desarrollador acepta paquetes autofirmados. Crea uno y **acuérdate de su subject**: el
`Publisher` del manifiesto tiene que coincidir letra por letra.

⚠ Aquí es donde de verdad importa no abrir la ventana «como administrador»: el certificado se crea en el
almacén del usuario que ejecuta la orden, así que una elevada lo pondría en el del administrador, y
`signtool`, corriendo como tú, no lo encontraría.

> **Dónde se escribe esto:** en **PowerShell** —pulsa la tecla **Windows**, escribe `powershell` y pulsa
> **Enter**— en una ventana **normal**: no hace falta «ejecutar como administrador». Desde cualquier
> carpeta.

```powershell
$c = New-SelfSignedCertificate -Type Custom -Subject "CN=TuNombre" `
       -KeyUsage DigitalSignature -FriendlyName "Firma UWP" `
       -CertStoreLocation "Cert:\CurrentUser\My" `
       -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
$c.Thumbprint     # esto es lo que se pasa como -Certificado
```

Después abre `package/Package.appxmanifest` y cambia los dos `CHANGE-ME`:

```xml
<Identity Name="BloodyRoar2-Recomp" Publisher="CN=TuNombre" ProcessorArchitecture="x64" Version="1.0.0.0" />
...
<PublisherDisplayName>TuNombre</PublisherDisplayName>
```

El empaquetador compara los dos antes de hacer nada y se detiene si no coinciden, lo que te ahorra
enterarte en el paso de `signtool`.

---

## 4. Aplicar el perfil de UWP

La carpeta de este repositorio es la que tiene `tools\` y `docs\` dentro:

> **Dónde se escribe esto:** en **PowerShell** —pulsa la tecla **Windows**, escribe `powershell` y pulsa
> **Enter**— en una ventana **normal**: no hace falta «ejecutar como administrador». Desde la carpeta de
> este repositorio.

```powershell
python tools\apply_uwp.py <raíz del proyecto del juego>
python tools\apply_uwp.py --list      # los trece pasos, en orden, y para qué es cada uno
```

Copia la entrada WinRT en `<proyecto>\UWP\` y ejecuta los trece parches en orden; el quinto es el que
registra esa entrada en el `CMakeLists.txt` del propio juego. Cada paso es idempotente y comprueba lo que
espera encontrar, así que pasarlo dos veces no cambia nada y, si un paso no reconoce el árbol, se detiene
ahí en vez de dejarlo a medias.

Qué cambia y por qué cada cosa: [`HOW-IT-WORKS.es.md`](HOW-IT-WORKS.es.md).

---

## 5. Configurar y compilar

> **Dónde se escribe esto:** en **PowerShell** —pulsa la tecla **Windows**, escribe `powershell` y pulsa
> **Enter**— en una ventana **normal**: no hace falta «ejecutar como administrador». Desde la carpeta de
> este repositorio.

```powershell
powershell -ExecutionPolicy Bypass -File tools\configurar-uwp.ps1 `
     -Raiz <proyecto> -Build <compilación> -Sdl2 <carpeta cmake de SDL2> -Compilar
```

Entra en el entorno de UWP (`vcvarsall x64 uwp`, encontrado con `vswhere`) y configura con **Ninja**. No
con el generador de Visual Studio: es multiconfiguración, y este framework escribe un archivo de versión
por configuración, que CMake rechaza con *«Evaluation file to be written multiple times»*.

`vcvarsall x64 uwp` importa por sí solo: pone en `LIB` el CRT del App Container, así que el ejecutable
importa `msvcp140_app.dll` en vez del `msvcp140.dll` de escritorio. Con `vcvars64` el paquete se instala
y la consola se niega a lanzarlo.

**El objetivo es `psx-runtime-us`**, el de la región USA. Este proyecto tiene un objetivo por región
—Europa, USA, Japón y uno universal— y un paquete lleva el ejecutable de uno solo; el universal
necesitaría además el C de las otras regiones, y eso solo sale de sus discos. Si tu volcado es de otra
región, pasa `-Objetivo psx-runtime-<región>` y cambia el objetivo y el `OUTPUT_NAME` de
`tools\parche_uwp_cmake_juego.py`.

Sale `BloodyRoar2_Recompiled_USA.exe` en la carpeta de compilación.

---

## 6. Los mosaicos del paquete

Pon tus PNG en `package/Assets/`. Este repositorio no trae ninguno: los nombres y las medidas exactas
están en [`ASSETS.es.md`](ASSETS.es.md). Imágenes de un color plano sirven. El empaquetador se detiene y
te dice cuál falta.

---

## 7. Empaquetar y firmar

> **Dónde se escribe esto:** en **PowerShell** —pulsa la tecla **Windows**, escribe `powershell` y pulsa
> **Enter**— en una ventana **normal**: no hace falta «ejecutar como administrador». Desde la carpeta de
> este repositorio.

```powershell
powershell -ExecutionPolicy Bypass -File tools\empaquetar-uwp.ps1 `
     -Build <compilación> -Salida <salida> -Certificado <huella> -Version 1.0.0.0
```

Reúne el ejecutable, el manifiesto, tus mosaicos, la configuración inicial (el
`config\settings.toml` de este repositorio, más el `game_us.toml` y el `game_options.toml` que dejó la
compilación), el catálogo de mods incluido y la OpenBIOS libre; rehace `resources.pri` con `makepri` —sin
el bloque `<packaging>` de la configuración por defecto, que parte el PRI por escala y hace que la
consola lo rechace—; empaqueta con `makeappx`; y firma con tu certificado.

También escribe `mods\state.toml` con el **panorámico encendido**, porque en una consola no hay pestaña
Mods donde marcarlo. `-SinPanoramico` lo deja apagado. Apunta `-VCLibs` a
`Microsoft.VCLibs.x64.14.00.appx` para que se copie al lado de la salida y lo tengas a mano al instalar,
y `-Ajustes` a otro `settings.toml` si quieres otros valores de fábrica.

Sale `<identidad>_<versión>_x64.msix`, unos 8,9 MB. **El disco no va dentro**: va a la consola aparte, en
el paso 9.

> ⚠ **Sube `-Version` en cada instalación, sin excepción.** Instalar la **misma** versión encima
> **desregistra** el paquete: el portal responde «operación completada con éxito» y después el paquete
> desaparece de la lista, deja de resolverse por nombre y la app no se puede lanzar. Y un «Success» del
> portal no demuestra que quedó registrado: compruébalo listando después.

---

## 8. Instalarlo en la consola

### 8.1 La dependencia: VCLibs

El ejecutable importa el CRT del App Container —`msvcp140_app.dll`, `vcruntime140_app.dll`,
`vccorlib140_app.dll`—, que no vive en el paquete sino en un **paquete de marco** que hay que instalar
una vez en la consola. El manifiesto lo declara:

```xml
<PackageDependency Name="Microsoft.VCLibs.140.00" MinVersion="14.0.33519.0"
                   Publisher="CN=Microsoft Corporation, O=Microsoft Corporation, L=Redmond, S=Washington, C=US" />
```

**El archivo que hace falta es `Microsoft.VCLibs.x64.14.00.appx`** (unos 900 KB). Ya lo tienes: el SDK de
Windows y Visual Studio lo instalan aquí —

```text
C:\Program Files (x86)\Microsoft SDKs\Windows Kits\10\ExtensionSDKs\Microsoft.VCLibs\14.0\Appx\Retail\x64\Microsoft.VCLibs.x64.14.00.appx
```

⚠ **Hay dos archivos fáciles de coger por error y ninguno sirve:**

- `Microsoft.VCLibs.x64.14.00.Desktop.appx`, al que enlaza `aka.ms`, es la compilación del **Desktop
  Bridge**. Es otro paquete, y la consola seguirá diciendo que falta la dependencia.
- `…\Appx\**Debug**\x64\Microsoft.VCLibs.x64.Debug.14.00.appx` solo vale para paquetes firmados en
  configuración Debug. Este port compila en Release.

Se instala **una vez por consola**: los paquetes posteriores, y las versiones posteriores de este, ya lo
encuentran.

### Antes de tocar nada: cómo tiene que estar la consola

- **En modo desarrollador**, con Dev Home instalado. Si no lo está, eso es un trámite aparte con
  Microsoft y esta guía no lo cubre.
- **Encendida y con tu perfil con sesión iniciada.** ⚠ Sin un usuario conectado la consola **no abre
  aplicaciones**: el paquete se instala, aparece en la lista, y lanzarlo no hace nada. Es una de las
  cosas que más cuesta averiguar por uno mismo.
- **En la misma red que tu PC.**
- **Su dirección**, que **Dev Home** te enseña en la propia consola. El Device Portal escucha en el
  puerto **11443** por HTTPS.
- **Usuario y contraseña del portal**: los que pusiste en **Dev Home → Remote Access Settings** al
  activar el acceso remoto.

### 8.2 Subirlo

Abre `https://<ip-de-la-consola>:11443` en el navegador de tu PC.

⚠ El navegador avisará de que **el certificado del sitio no es de confianza**. Es normal y no es un
problema: el certificado es de la consola, que se lo emite ella misma. Entra igual —en Edge y Chrome,
**Configuración avanzada** → **Continuar a … (no seguro)**; en Firefox, **Avanzado** → **Aceptar el
riesgo y continuar**—. Después pedirá el usuario y la contraseña del portal.

Una vez dentro, **My games & apps → Add**:

1. **App package** → tu `.msix`.
2. **Certificate** → no hace falta: el paquete está firmado y el modo desarrollador lo acepta.
3. **Optional packages / Dependency** → aquí se añade `Microsoft.VCLibs.x64.14.00.appx`, la primera vez.
4. **Next → Install**, y esperar a *Package successfully registered*.

Después **lánzalo una vez** y deja que se cierre o ciérralo tú: ese primer arranque es lo que crea la
carpeta de datos de la aplicación, que es donde va el disco en el paso 9.

### 8.3 Si dice `There is not enough space on the disk`

No es que tu consola esté llena, y el mensaje engaña. **La primera instalación de una familia de
paquetes va a `D:\DevelopmentFiles`**, una partición de unos 5 GB que el modo desarrollador reserva justo
para eso; las *actualizaciones* posteriores de una familia ya registrada van a otro sitio. Esa partición
se llena con la primera versión de todo lo que hayas instalado por fuera de la tienda, y
**desinstalar un juego no la vacía**: las carpetas se quedan.

Así que el arreglo es que tu paquete llegue como **actualización** en vez de como primera instalación,
con una *semilla*:

> Una **semilla** es un paquete con la **misma identidad** que el de verdad —mismo `Identity Name` y
> mismo `Publisher`— pero con una **versión más baja** y un **ejecutable minúsculo** dentro. Nunca tiene
> que ejecutarse. Su único trabajo es registrar la familia en la consola, baratito, para que el paquete
> de verdad llegue como actualización.

1. Haz una carpeta con cualquier `.exe` pequeño renombrado a `BloodyRoar2_Recompiled_USA.exe` (un par de
   MB sobran: no se lanza nunca), y dale la carpeta `mods\bundled` que el empaquetador espera, aunque
   esté vacía:

   ```powershell
   New-Item -ItemType Directory -Force <semilla>\mods\bundled | Out-Null
   Copy-Item C:\Windows\System32\notepad.exe <semilla>\BloodyRoar2_Recompiled_USA.exe
   ```

2. Empaquétala con una **versión más baja** que la de verdad, todo lo demás igual:

   ```powershell
   powershell -ExecutionPolicy Bypass -File tools\empaquetar-uwp.ps1 `
        -Build <semilla> -Salida <salida> -Certificado <huella> -Version 0.0.0.1
   ```

3. Instala primero esa (8.2), con la dependencia de VCLibs.
4. Después instala el de verdad con su versión, más alta, y el portal lo toma como actualización. Entra.

### Quitarlo de la consola

⚠ **Tus partidas se van con él.** Viven dentro del paquete, en su `LocalState`, y desaparecen con él.
Para conservarlas, bájalas antes desde el **File explorer** del Device Portal: están en
`LocalState\PSXRecomp\SCUS-94424\saves`.

Para desinstalar, en el Device Portal: **My games & apps**, busca el juego en la lista y **Remove**. En
tu PC no se toca nada.

Si lo que quieres es **actualizar** sin perderlas, no desinstales: instala encima un paquete con una
**versión más alta**.

---

## 9. El disco

Vive en la carpeta de datos de la propia aplicación, que creó ese primer arranque:

```text
…\Packages\<identidad>\LocalState\PSXRecomp\SCUS-94424\
    disc\    bios\    saves\    logs\
```

Se sube por el **File explorer** del Device Portal → **LocalAppData** → tu paquete → `LocalState` →
`PSXRecomp` → `SCUS-94424` → `disc`:

- el `.cue`, tal cual;
- el `.bin`, **partido en trozos**. El portal responde 500 a una subida de 527 MiB porque la hace pasar
  por `D:\DevelopmentFiles`. `tools\partir_disco.py` lo corta en piezas de 150 MiB —cuatro para este
  juego— con los nombres `<disco>.bin.parte1`, `.parte2`, …:

  ```powershell
  python tools\partir_disco.py "<tu disco>.bin" <carpeta de salida> 150
  ```

  La entrada WinRT las une en el siguiente arranque, una sola vez, y deja las partes donde están. El
  registro dice `partes: 4 unidas, 552729408 bytes` cuando salió bien. Luego puedes borrar las partes de
  la consola.

**No hace falta subir ninguna BIOS**: la OpenBIOS libre viaja dentro del paquete. Si prefieres tu BIOS
retail, ponla en `bios\` y el runtime la usará.

En cada arranque la entrada WinRT también siembra `game_us.toml`, `game_options.toml` y los mods desde
dentro del paquete (así una versión nueva de verdad los actualiza), deja en paz `settings.toml`,
`input.ini` y `keybinds.ini` si ya existen (son tuyos), escribe `bios.cfg` y `disc.cfg` con rutas
**absolutas**, y desvía la salida del runtime a `logs\salida.txt` y `logs\errores.txt`.

Lee esos dos registros. En una consola son lo único que tienes.

⚠ **Los registros están bloqueados mientras el juego corre.** Para leerlos, para la aplicación primero.

---

## Si algo va mal

| Síntoma | Causa |
|---|---|
| `Failed to launch the application` | Lo causan varias cosas y cada una tapa a la siguiente; el §1 de [`HOW-IT-WORKS.es.md`](HOW-IT-WORKS.es.md) las lista. Las dos más comunes: la **dependencia de VCLibs** ausente o el archivo equivocado, y haber compilado con `vcvars64` en vez de `vcvarsall x64 uwp` |
| El paquete se instala pero no hay ventana | Mira `logs\errores.txt`. Si dice `Could not initialize OpenGL / GLES library`, el dibujo por software no se forzó antes de crear la ventana: el paso 4 no terminó |
| Se instaló bien y ahora la app no está en la lista | Instalaste **la misma versión** dos veces. Eso desregistra el paquete. Rehaz el paquete con una `-Version` más alta |
| `cannot launch with selected mods: package does not target this game/image: br2.enhancement.widescreen` | Los mods se validan antes de resolver el disco. El empaquetador quita la clave `disc` del `game_us.toml` que va dentro y `parche_uwp_disco_mods.py` lo resuelve antes; si rehiciste el paquete a mano, esa clave probablemente volvió. La prueba rápida es `-SinPanoramico`: si arranca sin el mod, es esto |
| El mando no hace nada | Las dos ranuras tienen que estar en «auto» (`parche_uwp_mando.py`, y el `config\settings.toml`). El registro dice `opened controller for slot:` cuando funciona |
| No se guarda nunca nada | `memcard_dir` es relativa y se resuelve contra la carpeta de instalación, de solo lectura. `parche_uwp_escritura.py` la vuelve a anclar; el registro confirma la carpeta escribible |
| El panorámico no engancha | Está encendido, pero el runtime lo aplica **al entrar al juego**: la demostración de atracción sigue en 4:3 aunque el registro diga `mod selected fixed display aspect 16:9`. Se comprueba jugando, no con una captura del arranque |
| El juego reinicia al volver de Home | Es lo esperado: el modo desarrollador termina un juego que pasa a segundo plano, y atar la maquinaria de estados al estado de activación no está hecho en este port. Está abierto como issue |
| Las peleas por debajo de 60 FPS | Conocido y sin resolver: ver el README. El rasterizador por software se queda sin tiempo en las escenas más cargadas |
