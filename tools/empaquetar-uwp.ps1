<#
  Arma el paquete UWP (.msix) de Bloody Roar II para la Xbox en modo desarrollador, con el ejecutable que
  deja configurar-uwp.ps1, la definición de package\ de este repositorio (identidad y TUS mosaicos), los
  archivos de configuración que siembran la carpeta de datos en el primer arranque, el catálogo de mods que
  trae la compilación y el panorámico encendido de fábrica.

  Rehace resources.pri con makepri —sin el bloque <packaging> de la configuración por defecto, que parte
  el PRI por escala—, empaqueta con makeappx y firma con TU certificado.

  El disco NO va dentro: se sube a la carpeta de datos de la consola, partido (docs\INSTALL.es.md).

  Uso (con la PowerShell que trae Windows; pwsh 7 también vale):
    powershell -ExecutionPolicy Bypass -File empaquetar-uwp.ps1 -Build <compilación> -Salida <carpeta> `
         -Certificado <huella SHA-1 del certificado en Cert:\CurrentUser\My> [-Version 1.0.0.1] `
         [-Ajustes <settings.toml>] [-VCLibs <Microsoft.VCLibs.x64.14.00.appx>] [-SinPanoramico] [-Conservar]

  ⚠ SUBE LA VERSIÓN EN CADA INSTALACIÓN. Reinstalar la misma versión encima desregistra el paquete: el
  Device Portal responde «operación completada con éxito» y después el paquete desaparece de la lista, deja
  de resolverse por nombre y la app no se puede lanzar. -Version cambia la versión solo en la copia que va
  al paquete; el manifiesto de package\ es del repositorio y no se modifica.

  -Certificado es la huella (thumbprint) de TU certificado de firma, el mismo cuyo CN tiene que coincidir
  con el Publisher del manifiesto. Cómo crear uno autofirmado: docs\INSTALL.es.md §3.
  -Conservar deja en %TEMP% la carpeta de trabajo, que por defecto se borra porque lleva dentro el
  ejecutable del juego.
#>
param(
    [Parameter(Mandatory)][string]$Build,
    [Parameter(Mandatory)][string]$Salida,
    [Parameter(Mandatory)][string]$Certificado,
    [string]$Version = '',
    [string]$Ejecutable = 'BloodyRoar2_Recompiled_USA.exe',
    [string]$Ajustes = '',
    [string]$VCLibs = '',
    [string]$Sdk = '',
    [switch]$SinPanoramico,
    [switch]$Conservar
)
$ErrorActionPreference = 'Stop'

$repo = Split-Path $PSScriptRoot                                   # la raíz de este repositorio
$def = Join-Path $repo 'package'                                   # manifiesto y mosaicos
if (-not $Ajustes) { $Ajustes = Join-Path $repo 'config\settings.toml' }

# El SDK de Windows: la versión más nueva que haya, salvo que se pase -Sdk.
if (-not $Sdk) {
    $bin = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin'
    if (Test-Path -LiteralPath $bin) {
        $Sdk = Get-ChildItem -LiteralPath $bin -Directory -Filter '10.*' |
               Sort-Object Name -Descending |
               ForEach-Object { Join-Path $_.FullName 'x64' } |
               Where-Object { Test-Path (Join-Path $_ 'makeappx.exe') } |
               Select-Object -First 1
    }
}
if (-not $Sdk -or -not (Test-Path -LiteralPath (Join-Path $Sdk 'makeappx.exe'))) {
    throw 'no encuentro el SDK de Windows 10/11 (makeappx, makepri, signtool): pasa -Sdk con la carpeta x64 de su bin'
}

$exe = Join-Path $Build $Ejecutable
if (-not (Test-Path -LiteralPath $exe)) { throw "falta el ejecutable de la consola: $exe (configurar-uwp.ps1 -Compilar)" }
if (-not (Test-Path -LiteralPath $Ajustes)) { throw "falta la configuración de la consola: $Ajustes" }

# El arte no viaja en este repositorio: lo pone quien empaqueta (docs\ASSETS.md).
#
# Los mosaicos que hacen falta se leen del XML —de sus atributos y de sus nodos de texto, que es
# donde van: `Square150x150Logo="Assets\…"` el primero, `<Logo>Assets\…</Logo>` el segundo—, y NO con
# una expresión regular sobre el archivo entero. Esa encuentra también los que están dentro de un
# comentario XML (el mosaico ancho lo está, porque es opcional) y entonces el empaquetado se detiene
# pidiendo un PNG que el paquete no usa. Los comentarios no son ni atributos ni texto, así que así no
# aparecen.
$manRuta = Join-Path $def 'Package.appxmanifest'
$man = [IO.File]::ReadAllText($manRuta)
[xml]$manXml = $man
$valores = @()
$valores += $manXml.SelectNodes('//@*')     | ForEach-Object { $_.Value }
$valores += $manXml.SelectNodes('//text()') | ForEach-Object { $_.Value }
$exigidos = $valores | Where-Object { $_ -and $_.Trim() -match '\.png$' } |
            ForEach-Object { Split-Path $_.Trim() -Leaf } | Sort-Object -Unique
$faltan = $exigidos | Where-Object { -not (Test-Path -LiteralPath (Join-Path $def "Assets\$_")) }
if ($faltan) {
    throw ("faltan mosaicos en package\Assets\: {0}. Este repositorio no distribuye arte del juego; " +
           "pon los tuyos con las medidas de docs\ASSETS.md" -f ($faltan -join ', '))
}

# -Version solo cambia la copia que va al paquete: el manifiesto de package\ es del repositorio y
# no se toca, para que empaquetar no deje el árbol modificado ni herede la versión a quien lo use después.
if ($Version) {
    $man = [regex]::Replace($man, '(<Identity[^>]*\bVersion=")[0-9.]+(")', "`${1}$Version`${2}")
}
if ($man -notmatch '<Identity Name="([^"]+)"[\s\S]*?Version="([0-9.]+)"') { throw 'no encuentro la identidad en el manifiesto' }
$familia, $version = $Matches[1], $Matches[2]

# Aviso temprano: si el CN del certificado no es el Publisher del manifiesto, signtool falla al final.
if ($man -match 'Publisher="([^"]+)"') {
    $publisher = $Matches[1]
    $cert = Get-ChildItem -LiteralPath "Cert:\CurrentUser\My\$Certificado" -ErrorAction SilentlyContinue
    if (-not $cert) { throw "no encuentro el certificado $Certificado en Cert:\CurrentUser\My" }
    if ($cert.Subject -ne $publisher) {
        throw ("el Publisher del manifiesto ($publisher) no es el del certificado ($($cert.Subject)): " +
               'la consola rechaza el paquete. Pon tu CN en package\Package.appxmanifest')
    }
}

# 1. el contenido del paquete
$trabajo = Join-Path $env:TEMP ('bloodyroar2-uwp-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
$cont = Join-Path $trabajo 'contenido'
New-Item -ItemType Directory -Force (Join-Path $cont 'Assets') | Out-Null
Copy-Item -LiteralPath $exe -Destination $cont
# El manifiesto del paquete sale de $man, que es donde -Version ya aplicó el cambio.
[IO.File]::WriteAllText((Join-Path $cont 'AppxManifest.xml'), $man)
Get-ChildItem -LiteralPath (Join-Path $def 'Assets') -File -Filter *.png | Copy-Item -Destination (Join-Path $cont 'Assets') -Force

# Configuración inicial (el primer arranque la copia a la carpeta de datos). game_us.toml y
# game_options.toml los deja la compilación al lado del ejecutable; settings.toml es el de este
# repositorio, que es el que deja el mando en «auto» y salta el lanzador.
foreach ($n in 'game_us.toml', 'game_options.toml', 'input.ini', 'keybinds.ini') {
    $r = Join-Path $Build $n
    if (Test-Path -LiteralPath $r) { Copy-Item -LiteralPath $r -Destination $cont }
}
Copy-Item -LiteralPath $Ajustes -Destination (Join-Path $cont 'settings.toml')

# El disco: en la consola NO es el del game_us.toml (ahí está la ruta del PC de quien generó el proyecto).
# Lo señala disc.cfg, que escribe la entrada WinRT con la ruta real de la carpeta de datos. Hay que quitar
# la clave: el runtime arranca igual sin ella, pero si se deja, es ESA ruta la que le pasa al sistema de
# mods, y entonces ningún paquete con huella de disco llega a aplicarse («package does not target this
# game/image») — y aquí el panorámico es justo uno de esos, con el SHA-256 del disco en su manifiesto.
$gt = Join-Path $cont 'game_us.toml'
if (Test-Path -LiteralPath $gt) {
    $txt = [IO.File]::ReadAllText($gt)
    $antes = $txt
    $txt = [regex]::Replace($txt, '(?m)^(\s*disc\s*=\s*".*"\s*)$',
        "# (Xbox) el disco lo señala disc.cfg, que escribe la entrada WinRT con la ruta de los datos:`r`n#`$1")
    if ($txt -eq $antes) { throw 'no encontré la clave disc en game_us.toml: revisar antes de empaquetar' }
    [IO.File]::WriteAllText($gt, $txt)
}

# Los mods: el catálogo entero que preparó la compilación (en este proyecto viven en mods\bundled).
$modsDst = Join-Path $cont 'mods'
New-Item -ItemType Directory -Force $modsDst | Out-Null
$modsOrigen = Join-Path $Build 'mods\bundled'
if (-not (Test-Path -LiteralPath $modsOrigen)) { throw "falta el catálogo de mods: $modsOrigen" }
Copy-Item -LiteralPath $modsOrigen -Destination $modsDst -Recurse -Force

# El panorámico, encendido de fábrica: en la consola no hay pestaña Mods donde marcarlo. El aspecto no se
# declara aquí porque la opción del mod ya trae 16:9 por defecto en su propio manifiesto.
if (-not $SinPanoramico) {
    @'
format_version = 2

[[package]]
id = "br2.enhancement.widescreen"
version = "1.0.0"

[[feature]]
package_id = "br2.enhancement.widescreen"
id = "widescreen"
enabled = true
'@ | Set-Content -LiteralPath (Join-Path $modsDst 'state.toml') -Encoding utf8NoBOM
}

# La BIOS libre que trae el runtime (si quieres la SCPH-1001 retail, va a la carpeta de datos, no aquí).
$bios = Join-Path $Build 'bios'
if (Test-Path -LiteralPath $bios) { Copy-Item -LiteralPath $bios -Destination $cont -Recurse -Force }

# Las herramientas del SDK dicen en su salida POR QUÉ fallaron, así que no se descarta: se guarda y se
# muestra con el error. Un `| Out-Null` aquí deja un «makepri falló» sin una pista.
function Invoke-Sdk {
    param([string]$Exe, [string[]]$Argumentos, [string]$Que)
    $salida = & "$Sdk\$Exe" @Argumentos 2>&1
    if ($LASTEXITCODE) { throw ("$Que falló (código $LASTEXITCODE):`n" + ($salida -join "`n")) }
}

# 2. resources.pri con el nombre de esta identidad
$pri = Join-Path $trabajo 'priconfig.xml'
Invoke-Sdk 'makepri.exe' @('createconfig', '/cf', $pri, '/dq', 'en-US', '/o') 'makepri createconfig'
[xml]$cfg = Get-Content -LiteralPath $pri
foreach ($n in @($cfg.SelectNodes('//packaging'))) { [void]$n.ParentNode.RemoveChild($n) }
$cfg.Save($pri)
Invoke-Sdk 'makepri.exe' @('new', '/pr', $cont, '/cf', $pri, '/of', (Join-Path $cont 'resources.pri'), '/o') 'makepri new'

# 3. empaquetar y firmar
New-Item -ItemType Directory -Force (Join-Path $Salida 'Dependencies') | Out-Null
$msix = Join-Path $Salida "${familia}_${version}_x64.msix"
Invoke-Sdk 'makeappx.exe' @('pack', '/o', '/d', $cont, '/p', $msix) 'makeappx pack'
Invoke-Sdk 'signtool.exe' @('sign', '/fd', 'SHA256', '/sha1', $Certificado, '/s', 'My', $msix) 'signtool'
if ($VCLibs -and (Test-Path -LiteralPath $VCLibs)) {
    Copy-Item -LiteralPath $VCLibs -Destination (Join-Path $Salida 'Dependencies') -Force
}

'paquete: {0} ({1:N0} B, SHA-256 {2})' -f $msix, (Get-Item -LiteralPath $msix).Length, (Get-FileHash -LiteralPath $msix).Hash
'ejecutable: {0:N0} B, SHA-256 {1}' -f (Get-Item -LiteralPath $exe).Length, (Get-FileHash -LiteralPath $exe).Hash
'mods: ' + ((Get-ChildItem -LiteralPath (Join-Path $modsDst 'bundled') -Directory | ForEach-Object { $_.Name }) -join ', ')
'panorámico de fábrica: ' + (-not $SinPanoramico)

# La carpeta de trabajo lleva dentro el ejecutable del juego y los mods: no se deja en %TEMP%
# salvo que se pida con -Conservar para inspeccionar lo que se empaquetó.
if ($Conservar) {
    "trabajo (conservado): $trabajo"
} else {
    [IO.Directory]::Delete($trabajo, $true)
}
