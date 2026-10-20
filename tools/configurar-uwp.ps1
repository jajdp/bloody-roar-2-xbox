# Configura el proyecto de Bloody Roar II para Xbox (UWP) y, con -Compilar, lo compila.
# Usa Visual Studio 2022 como compilador pero con el generador **Ninja**: el de Visual Studio es
# multiconfiguración y este framework genera un archivo de versión por configuración que CMake rechaza
# («Evaluation file to be written multiple times»). SDL3 no tiene WinRT, así que va el backend SDL2 con un
# SDL2 2.30.2 compilado para WindowsStore (ver docs/INSTALL.es.md).
#
# El objetivo es `psx-runtime-us`, el de la región USA: este proyecto tiene un objetivo por región
# (Europa, USA, Japón y uno universal) y el paquete lleva el ejecutable de una sola. El universal exigiría
# además el C de las otras regiones, que solo sale de sus discos. Si tu volcado es otro, cambia -Objetivo y
# el OUTPUT_NAME de tools/parche_uwp_cmake_juego.py, y enciende el -DBR2_BUILD_* que toque.
#
#   -Raiz       el árbol del juego: la carpeta con CMakeLists.txt y game_us.toml
#   -Build      la carpeta de compilación, fuera del árbol
#   -Sdl2       el paquete de CMake de un SDL2 compilado para WindowsStore (la carpeta con SDL2Config.cmake)
#   -Objetivo   el objetivo de CMake a compilar (por defecto psx-runtime-us)
#   -VcVars     vcvarsall.bat de Visual Studio 2022; si no se pasa, se busca con vswhere
#   -Compilar   además de configurar, compila
#   -Limpio     borra la carpeta de compilación antes de empezar
# Uso (con la PowerShell que trae Windows; pwsh 7 también vale):
#   powershell -ExecutionPolicy Bypass -File configurar-uwp.ps1 -Raiz <árbol> -Build <compilación> -Sdl2 <cmake de SDL2> -Compilar
param(
    [Parameter(Mandatory)][string]$Raiz,
    [Parameter(Mandatory)][string]$Build,
    [Parameter(Mandatory)][string]$Sdl2,
    [string]$Objetivo = 'psx-runtime-us',
    [string]$VcVars,
    [switch]$Compilar,
    [switch]$Limpio
)
$ErrorActionPreference = 'Continue'
# El entorno tiene que ser el de UWP, no el de escritorio: `vcvarsall x64 uwp` pone en LIB las bibliotecas
# del CRT para App Container (lib\x64\store), que son las que importan msvcp140_app.dll, vcruntime140_app.dll y
# vccorlib140_app.dll —las que la consola tiene, por el paquete de VCLibs—. Con vcvars64 el ejecutable importaba
# las de escritorio (msvcp140.dll) y kernel32.dll, y no arrancaba: «Failed to launch the application».
$vcvars = $VcVars
if (-not $vcvars) {
    # vswhere viene con cualquier Visual Studio 2017+ y está siempre en la misma ruta.
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (Test-Path -LiteralPath $vswhere) {
        $vs = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
                         -property installationPath 2>$null | Select-Object -First 1
        if ($vs) { $vcvars = Join-Path $vs 'VC\Auxiliary\Build\vcvarsall.bat' }
    }
}
if (-not $vcvars -or -not (Test-Path -LiteralPath $vcvars)) {
    throw 'no encuentro vcvarsall.bat: pasa -VcVars con su ruta (Visual Studio 2022 con las herramientas de C++ y el SDK de UWP)'
}
if (-not (Test-Path -LiteralPath (Join-Path $Raiz 'game_us.toml'))) {
    throw "no parece el árbol del juego (falta game_us.toml): $Raiz"
}
if ($Limpio -and (Test-Path -LiteralPath $Build)) { Remove-Item -Recurse -Force -LiteralPath $Build }
New-Item -ItemType Directory -Force $Build | Out-Null
$registro = Join-Path $Build 'configurar.log'

# PSX_SETUP_WIZARD y PSX_NETPLAY solo obedecen a estas dos líneas si el CMake del juego está parcheado
# (tools/parche_uwp_cmake_juego.py): el proyecto los fija con FORCE, que pisa la línea de órdenes.
$opciones = @(
    "-S `"$Raiz`"", "-B `"$Build`"",
    '-G Ninja',
    '-DCMAKE_BUILD_TYPE=Release',
    '-DCMAKE_SYSTEM_NAME=WindowsStore', '-DCMAKE_SYSTEM_VERSION=10.0',
    '-DPSX_SDL_BACKEND=SDL2',
    "-DSDL2_DIR=`"$Sdl2`"",
    '-DPSX_DEBUG_TOOLS=OFF',
    '-DPSX_RECOMP_UI=OFF',
    '-DPSX_LAUNCHER=OFF',
    '-DPSX_ENABLE_VULKAN=OFF',
    '-DPSX_STATIC_RUNTIME=OFF',
    '-DPSX_NETPLAY=OFF',
    '-DPSX_SETUP_WIZARD=OFF',
    '-DBR2_BUILD_JAPAN=OFF',
    '-DBR2_BUILD_UNIVERSAL=OFF'
) -join ' '

$orden = "`"$vcvars`" x64 uwp >nul && cmake $opciones"
if ($Compilar) { $orden += " && cmake --build `"$Build`" --target $Objetivo" }
"orden: $orden" | Out-File -FilePath $registro -Encoding utf8
cmd /c $orden 2>&1 | Tee-Object -FilePath $registro -Append | Select-Object -Last 35
$codigo = $LASTEXITCODE
"`n== código de salida: $codigo  (registro completo: $registro)"
# El código se propaga: encadenar esto con el empaquetado tiene que pararse aquí si CMake falló.
# Solo se ven las últimas 35 líneas, así que un fallo pasa desapercibido si el script sale con 0.
exit $codigo
