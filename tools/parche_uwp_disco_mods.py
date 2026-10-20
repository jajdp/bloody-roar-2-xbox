# El disco, ANTES de validar los mods.
#
# El framework comprueba los paquetes de mods —y con ellos la huella del disco que cada uno exige— **antes** de
# resolver dónde está el disco de verdad: `mod_runtime_commit(resolved_disc)` ocurre antes de que `resolved_disc`
# tenga la ruta real. En el PC no se nota, porque a esas alturas ya trae la que el game_us.toml del proyecto lleva
# escrita. En la consola esa ruta no puede existir: el disco vive en la carpeta de datos del paquete y su ruta
# depende de la instalación, así que el empaquetado quita la clave. Resultado: el sistema de mods calcula la huella
# de un disco vacío y **rechaza el arranque**:
#     psxrecomp: cannot launch with selected mods: package does not target this game/image: br2.enhancement.widescreen
# Y aquí eso es fatal, no molesto: el panorámico va encendido de fábrica —en la consola no hay pestaña Mods donde
# marcarlo— y su manifiesto lleva el SHA-256 del disco de las tres regiones, así que el juego no llega ni a arrancar.
#
# El parche resuelve el disco desde `disc.cfg` —el puntero que escribe la entrada WinRT con la ruta real, después
# de unir las partes subidas— justo antes de esa comprobación, y solo cuando hace falta.
#
# ⚠ El ancla no es la del port de Street Fighter EX2 Plus: entre los dos commits del framework el bloque del juego
# en red se reescribió entero y su comentario es otro, así que el ancla heredada daba «0 apariciones». La llamada a
# `mod_runtime_commit` sigue donde estaba, pero ahora cuelga de un if-else con el plan del lanzador.
#
# Idempotente y todo o nada; escritura atómica.
# Uso: parche_uwp_disco_mods.py <raíz del proyecto del juego>
import parchear

MARCA = 'Recompilaciones (2026-10-19): UWP - disc before mods'

VIEJO = '''    {
        /* Netplay plan handling. The launcher UI runs provider_commit_netplay'''

NUEVO = '''#if defined(PSX_UWP)
    /* ''' + MARCA + '''. Mods are validated below, but on the console the disc
     * path cannot come from game_us.toml - it lives in the package's data folder and depends on the install, so
     * the packaging step drops the key. Resolve it from the disc.cfg sidecar (written by the WinRT entry point
     * after joining the uploaded parts) before the check; otherwise every package that targets a disc digest
     * fails with "does not target this game/image" and, with the widescreen mod on by default, the runtime
     * refuses to launch at all. */
    if (resolved_disc.empty() || !std::filesystem::exists(resolved_disc)) {
        std::filesystem::path uwp_disc = read_cached_path(argv[0], "disc.cfg");
        if (!uwp_disc.empty()) {
            uwp_disc = normalize_disc_path_for_launch(uwp_disc);
            if (std::filesystem::exists(uwp_disc)) {
                resolved_disc = uwp_disc;
                std::fprintf(stdout, "psxrecomp: UWP - disc for mods: %s\\n",
                             resolved_disc.string().c_str());
            }
        }
    }
#endif
    {
        /* Netplay plan handling. The launcher UI runs provider_commit_netplay'''


def main():
    parchear.informe(parchear.aplicar(
        parchear.runtime(parchear.raiz(), 'src', 'main.cpp'),
        [(VIEJO, NUEVO)], MARCA, 'main.cpp: en la consola, el disco se resuelve antes de comprobar los mods'))


if __name__ == '__main__':
    main()
