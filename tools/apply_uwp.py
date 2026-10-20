#!/usr/bin/env python3
"""Aplica el perfil UWP completo a un árbol de Bloody Roar II (BloodyRoar2Recomp + psxrecomp).

Uso:
    python tools/apply_uwp.py <raíz del proyecto del juego>
    python tools/apply_uwp.py --list

La raíz es la carpeta con CMakeLists.txt y game_us.toml. Cada paso es idempotente y comprueba lo que
espera encontrar antes de escribir, así que pasarlo dos veces no cambia nada y, si un paso no reconoce
el árbol, se detiene ahí en vez de dejarlo a medias.

Después de esto: tools/configurar-uwp.ps1 (configura y compila) y tools/empaquetar-uwp.ps1 (empaqueta y
firma). Ver docs/INSTALL.es.md.

Recompilaciones — https://github.com/jajdp/bloody-roar-2-xbox
PolyForm Noncommercial License 1.0.0
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERR = os.path.join(REPO, 'tools')
ENTRADA = os.path.join(REPO, 'src', 'SDL_winrt_main_NonXAML.cpp')

PROYECTO_BASE = 'novapowers0/BloodyRoar2Recomp'

# Los pasos informan en castellano, con acentos, y la consola de Windows arranca en una página de
# códigos que no los tiene (cp1252 o cp850): sin esto, imprimir el informe de un paso levanta un
# UnicodeEncodeError y el perfil se interrumpe a media aplicación. Se arregla aquí, para la salida
# propia, y en el entorno de los subprocesos, para la suya.
for flujo in (sys.stdout, sys.stderr):
    if hasattr(flujo, 'reconfigure'):
        flujo.reconfigure(encoding='utf-8', errors='replace')
ENTORNO_HIJOS = dict(os.environ, PYTHONIOENCODING='utf-8:replace', PYTHONUTF8='1')

# El orden importa, y es el que se verificó contra el árbol del que salió el paquete que corre en la
# consola: el perfil primero —porque enciende PSX_UWP, que es de lo que cuelgan todas las guardas—,
# luego los dos de código del framework, el CMake del juego en cuanto la entrada WinRT está puesta, y
# al final los del runtime, que se reparten anclas distintas del mismo main.cpp.
PASOS = [
    ('parche_uwp.py',                 'el perfil UWP del runtime (runtime.cmake)'),
    ('parche_uwp_gl.py',              'quitar la importación de OPENGL32.dll (backend GL inerte)'),
    ('parche_uwp_codigo.py',          'las guardas de código del perfil (diálogos y estado de activación)'),
    ('parche_uwp_codigo_br2.py',      'los cinco arreglos que pide este framework en App Container'),
    ('parche_uwp_cmake_juego.py',     'el CMake del juego: los dos FORCE y la entrada WinRT'),
    ('parche_uwp_rutas.py',           'anclar los archivos del runtime en la carpeta de datos'),
    ('parche_uwp_render_software.py', 'fijar el renderizador por software antes de crear la ventana'),
    ('parche_uwp_disco_mods.py',      'resolver el disco antes de validar los mods'),
    ('parche_uwp_escritura.py',       'tarjetas de memoria y estados en una carpeta donde se pueda escribir'),
    ('parche_uwp_mando.py',           'todas las ranuras en «auto»: en la consola no hay teclado'),
    ('parche_uwp_osd.py',             'la capa visual del contador de FPS, sin lanzador'),
    ('parche_uwp_fps_encendido.py',   'el contador, encendido de fábrica'),
    ('parche_uwp_fps_r3.py',          'R3 conmuta el contador'),
]


def main():
    if '--list' in sys.argv[1:]:
        print('El perfil UWP, en orden:\n')
        print('  %-32s %s' % ('(entrada WinRT)', 'src/SDL_winrt_main_NonXAML.cpp -> <árbol>/UWP/'))
        for n, (script, que) in enumerate(PASOS, 1):
            print('  %2d. %-28s %s' % (n, script, que))
        print('\nLa entrada se registra en el CMakeLists del juego en el paso 5.')
        return 0

    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    if len(args) != 1:
        sys.exit('uso: %s <ruta de la raiz del proyecto del juego>   (--list para ver los pasos)'
                 % os.path.basename(sys.argv[0]))
    raiz = os.path.abspath(args[0])
    for exigido in ('CMakeLists.txt', 'game_us.toml'):
        if not os.path.isfile(os.path.join(raiz, exigido)):
            sys.exit('no es la raíz de un proyecto del juego (falta %s): %s' % (exigido, raiz))
    if not os.path.isfile(ENTRADA):
        sys.exit('falta en el repositorio: %s' % ENTRADA)

    hechos = []

    # 1. La entrada WinRT. El archivo se copia aquí; quien lo registra en el CMakeLists del juego es
    #    parche_uwp_cmake_juego.py, que se detiene si no lo encuentra puesto.
    destino = os.path.join(raiz, 'UWP', 'SDL_winrt_main_NonXAML.cpp')
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(ENTRADA, 'rb') as f:
        fuente = f.read()
    actual = None
    if os.path.isfile(destino):
        with open(destino, 'rb') as f:
            actual = f.read()
    if actual != fuente:
        with open(destino, 'wb') as f:
            f.write(fuente)
        hechos.append('UWP/SDL_winrt_main_NonXAML.cpp')

    # 2. Los parches, en orden.
    for script, que in PASOS:
        ruta = os.path.join(HERR, script)
        if not os.path.isfile(ruta):
            sys.exit('falta en el repositorio: tools/%s' % script)
        print('-- %-30s %s' % (script, que))
        r = subprocess.run([sys.executable, ruta, raiz], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', env=ENTORNO_HIJOS)
        salida = (r.stdout or '').strip()
        if salida:
            print('\n'.join('   ' + l for l in salida.split('\n')))
        if r.returncode != 0:
            print((r.stderr or '').strip())
            sys.exit('\nse detuvo en %s (nada más se aplicó). El árbol no es el que este paso espera: '
                     'comprueba que es %s sin modificar y que los pasos anteriores están puestos.'
                     % (script, PROYECTO_BASE))
        if salida and 'ya estaba' not in salida:
            hechos.append(script)

    if hechos:
        print('\nListo: %d de los %d pasos escribieron algo; el resto ya estaba puesto.'
              % (len(hechos), len(PASOS) + 1))
    else:
        print('\nListo: el perfil UWP ya estaba aplicado entero, no hubo nada que cambiar.')
    print('Ahora: tools/configurar-uwp.ps1 para configurar y compilar (docs/INSTALL.es.md §4).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
