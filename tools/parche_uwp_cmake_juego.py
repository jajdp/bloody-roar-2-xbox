# Los dos cambios que pide el CMake DEL JUEGO (no el del framework) para compilar para la consola.
#
#   1. Que la línea de órdenes pueda apagar el asistente de arranque y el juego en red. El proyecto los
#      enciende con `set(... CACHE BOOL ... FORCE)`, y FORCE pisa lo que se pase por la línea de órdenes:
#      `-DPSX_SETUP_WIZARD=OFF` y `-DPSX_NETPLAY=OFF` no surtían efecto. En la consola los dos sobran: el
#      asistente y «Generate & rebuild» viven en recomp-ui, que en UWP no se compila, y el juego en red no
#      tiene dónde configurarse sin lanzador. Fuera de WindowsStore nada cambia.
#
#   2. La entrada WinRT. En UWP la aplicación no arranca por `main()`, sino por la entrada WinRT de SDL
#      (`src/SDL_winrt_main_NonXAML.cpp` de este repositorio, que `apply_uwp.py` copia a `<raíz>\UWP\`),
#      que hay que compilar con /ZW y declarar el ejecutable como aplicación de ventana. Sin esto el
#      enlazador pide el `main(Platform::Array<String^>^)` de vccorlib y corta con LNK2019. Con el
#      generador Ninja hay que ponerlo a mano: VS_WINRT_APPLICATION y VS_DEPLOYMENT_CONTENT son
#      propiedades del generador de Visual Studio.
#
# ⚠ El objetivo es `psx-runtime-us`, el de la región USA. Si tu volcado es el europeo o el japonés, cambia
#   aquí el objetivo y el OUTPUT_NAME, y configura con el `-DBR2_BUILD_*` que toque: el proyecto tiene un
#   objetivo por región y el paquete lleva el ejecutable de una sola.
#
# Las dos anclas son líneas del CMakeLists del proyecto del juego, que es MIT (ver NOTICE.md).
#
# Idempotente y todo o nada; escritura atómica.
# Uso: parche_uwp_cmake_juego.py <raíz del proyecto del juego>
import os
import sys

import parchear

MARCA = 'Recompilaciones (2026-10-19)'

CAMBIOS = [
    # 1. que la linea de ordenes pueda apagarlos
    ('''set(PSX_SETUP_WIZARD ON CACHE BOOL
    "Advertise first-run setup wizard + Generate & rebuild in recomp-ui" FORCE)
if(EXISTS "${PSXRECOMP_ROOT}/lib/recomp-net/CMakeLists.txt")
    set(PSX_NETPLAY ON CACHE BOOL "Netplay runtime wired (recomp-net present)" FORCE)
endif()''',
     '''# ''' + MARCA + ''': switchable when building for the console. The FORCE on these two
# overrode the command line, and there is no launcher on a console to configure them in. Outside
# WindowsStore they stay exactly as they were; in WindowsStore whatever is passed with -D wins.
if(NOT CMAKE_SYSTEM_NAME STREQUAL "WindowsStore")
    set(PSX_SETUP_WIZARD ON CACHE BOOL
        "Advertise first-run setup wizard + Generate & rebuild in recomp-ui" FORCE)
    if(EXISTS "${PSXRECOMP_ROOT}/lib/recomp-net/CMakeLists.txt")
        set(PSX_NETPLAY ON CACHE BOOL "Netplay runtime wired (recomp-net present)" FORCE)
    endif()
endif()'''),

    # 2. la entrada WinRT, antes del bloque de Japon (el ultimo del archivo)
    ('''if(BR2_BUILD_JAPAN)
    foreach(_PSX_RUNTIME_CONFIG game_japan.toml game_options.toml)''',
     '''# ''' + MARCA + ''': the console's entry point. In UWP the app does not start at main()
# but at SDL's WinRT entry point, which is compiled with /ZW; without it the linker asks for vccorlib's
# main(Platform::Array<String^>^) and stops with LNK2019. With the Ninja generator this has to be written
# by hand, because VS_WINRT_APPLICATION and VS_DEPLOYMENT_CONTENT belong to the Visual Studio generator.
# The target is the USA region's one, which is the region this port was built and tested for.
if(CMAKE_SYSTEM_NAME STREQUAL "WindowsStore")
    target_sources(psx-runtime-us PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/UWP/SDL_winrt_main_NonXAML.cpp")
    set_property(SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/UWP/SDL_winrt_main_NonXAML.cpp"
                 PROPERTY COMPILE_OPTIONS "/ZW")
    set_target_properties(psx-runtime-us PROPERTIES
        OUTPUT_NAME "BloodyRoar2_Recompiled_USA" WIN32_EXECUTABLE TRUE)
endif()

if(BR2_BUILD_JAPAN)
    foreach(_PSX_RUNTIME_CONFIG game_japan.toml game_options.toml)'''),
]


def main():
    raiz = parchear.raiz()
    # La entrada WinRT no sirve de nada si el archivo no esta donde se la pide.
    entrada = os.path.join(raiz, 'UWP', 'SDL_winrt_main_NonXAML.cpp')
    if not os.path.isfile(entrada):
        sys.exit('falta %s: lo copia apply_uwp.py desde src/ de este repositorio' % entrada)
    parchear.informe(parchear.aplicar(
        os.path.join(raiz, 'CMakeLists.txt'), CAMBIOS, MARCA,
        'CMakeLists.txt del juego: apagables el asistente y el juego en red, y la entrada WinRT registrada'))


if __name__ == '__main__':
    main()
