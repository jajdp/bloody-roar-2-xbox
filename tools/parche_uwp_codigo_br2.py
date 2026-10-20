# Los cinco arreglos que pide ESTE framework para compilar en App Container, y que el port hermano de
# Street Fighter EX2 Plus no necesitó: su revisión de psxrecomp es anterior y no traía ni los dos archivos
# de diagnóstico ni el guardia de inanición (583 líneas más solo en runtime.cmake).
#
#   1. runtime.cmake — atómicos de C11. El framework ya pasa /experimental:c11atomics, pero «scoped to the
#      one C source that needs it»: audio_trace.c. Con MSVC también lo necesita starvation_ring.c (el
#      guardia de inanición), y sin la opción MSVC corta con «C atomic support is not enabled». Son los dos
#      únicos .c del runtime que incluyen <stdatomic.h>.
#   2. runtime.cmake — el recurso del icono. `rc.exe` corta con «RC1107: invalid usage»: CMake le pasa los
#      -D del proyecto y el título de la ventana lleva espacios y paréntesis. En UWP el icono lo dan los
#      Assets del paquete, así que la rama de Windows se deja fuera del perfil de la consola.
#   3. crash_trace.c — `SetErrorMode` y sus constantes SEM_* no existen en App Container. La llamada solo
#      servía para que no saliera el cuadro de error de Windows antes del volcado; allí no hay tal cuadro.
#   4. freeze_heartbeat.c — el volcado de pila del hilo principal usa DbgHelp (SymInitialize, StackWalk64,
#      SymFromAddr, STACKFRAME64, SYMBOL_INFO), que no está en App Container. Los errores del compilador
#      caen todos dentro de `freeze_dump_main_stack_json`, y la función de varias muestras la llama en vez
#      de repetir el código, así que basta neutralizar esa: el latido se sigue escribiendo y el volcado de
#      pila va vacío, que es lo que ya hace cuando no puede resolver símbolos.
#   5. autocompile.c — la recompilación al vuelo lanza un proceso hijo con tuberías heredadas
#      (HANDLE_FLAG_INHERIT, STARTF_USESTDHANDLES), y en App Container no hay CreateProcess ni herencia de
#      descriptores. En la consola tampoco hay compilador que lanzar, así que basta sacar a UWP de la rama
#      de Windows: cae en la que el framework ya tiene para los demás sistemas, que devuelve 0 con «manual
#      compile flow only». Y el cierre igual, que usa TerminateJobObject.
#
# Y dos que son del propio framework, no de UWP, pero sin los cuales no enlaza con este perfil:
#
#   6. psx_fiber.c — el App Container solo exporta `CreateFiberEx` y `ConvertThreadToFiberEx`, no
#      `CreateFiber` ni `ConvertThreadToFiber`, y las fibras son el motor del planificador del BIOS.
#   7. main.cpp — el registro del lobby del juego en red se llama sin guarda: con `PSX_NETPLAY=OFF` su
#      archivo no se compila y el símbolo queda sin resolver (LNK2019 en SDL_main).
#
# Idempotente y todo o nada **sobre los seis archivos**: se comprueban todas las anclas antes de escribir
# ninguna, porque quedarse a medias aquí deja un árbol que no compila y que ya no se puede volver a parchear.
# Escritura atómica.
# Uso: parche_uwp_codigo_br2.py <raíz del proyecto del juego>
import parchear

MARCA = 'Recompilaciones (2026-10-19): UWP'

CMAKE = [
    # 1. los atomicos de C11, tambien para el guardia de inanicion
    ('''        set_property(SOURCE ${PSXRECOMP_ROOT}/runtime/src/audio_trace.c
            APPEND PROPERTY COMPILE_OPTIONS /experimental:c11atomics)''',
     '''        # ''' + MARCA + ''': starvation_ring.c includes <stdatomic.h> too, and without the
        # option MSVC stops with "C atomic support is not enabled". These are the only two .c files of the
        # runtime that use it.
        set_property(SOURCE ${PSXRECOMP_ROOT}/runtime/src/audio_trace.c
                            ${PSXRECOMP_ROOT}/runtime/src/starvation_ring.c
            APPEND PROPERTY COMPILE_OPTIONS /experimental:c11atomics)'''),

    # 2. sin recurso de icono en el PE: en UWP el icono lo dan los Assets del paquete
    ('''    if(PSXRT_APP_ICON AND EXISTS "${PSXRT_APP_ICON}")
        if(WIN32)''',
     '''    if(PSXRT_APP_ICON AND EXISTS "${PSXRT_APP_ICON}")
        # ''' + MARCA + ''': in UWP the executable's icon is never used (the package
        # Assets provide it) and the resource compiler stops with "fatal error RC1107: invalid usage",
        # because CMake passes it the project's -D defines and the window title has spaces and
        # parentheses. It falls through to the branch for the other systems, which only reports; the PNG
        # is still copied next to the exe.
        if(WIN32 AND NOT PSX_UWP)'''),
]

CRASH = [
    ('''    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);''',
     '''#if !defined(PSX_UWP)   /* ''' + MARCA + ''': neither SetErrorMode nor the SEM_* constants exist
                         * in the App Container, and there is no Windows error box there to suppress. */
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
#endif'''),
]

HEARTBEAT = [
    ('''static void freeze_dump_main_stack_json(FILE *f) {''',
     '''#if defined(PSX_UWP)
/* ''' + MARCA + ''': the App Container has no DbgHelp (SymInitialize, StackWalk64, SymFromAddr)
 * and does not allow walking another thread's stack. The heartbeat is still written in full; only the
 * stack dump comes out empty, just as it does on a PC when DbgHelp cannot resolve symbols. */
static void freeze_dump_main_stack_json(FILE *f) {
    if (f) fputs("[]", f);
}
#else
static void freeze_dump_main_stack_json(FILE *f) {'''),

    ('''    fputc(']', f);

    ResumeThread(s_main_thread);
}''',
     '''    fputc(']', f);

    ResumeThread(s_main_thread);
}
#endif  /* !PSX_UWP - ''' + MARCA + ''' */'''),
]

AUTOCOMPILE = [
    ('''    if (s_retry_not_before_ms &&
        autocompile_now_ms() < s_retry_not_before_ms) return 0;
#ifdef _WIN32''',
     '''    if (s_retry_not_before_ms &&
        autocompile_now_ms() < s_retry_not_before_ms) return 0;
/* ''' + MARCA + ''': the App Container has neither CreateProcess nor handle inheritance
 * (HANDLE_FLAG_INHERIT, STARTF_USESTDHANDLES), and there is no compiler to spawn on a console anyway. It
 * falls into the branch the framework already has for the other systems: "manual compile flow only". */
#if defined(_WIN32) && !defined(PSX_UWP)'''),

    ('''void autocompile_shutdown(void) {
#ifdef _WIN32''',
     '''void autocompile_shutdown(void) {
/* ''' + MARCA + ''': no TerminateJobObject in the App Container. Since the request never
 * spawns a child process (see above), there is nothing to stop here: the function is empty on a console. */
#if defined(_WIN32) && !defined(PSX_UWP)'''),
]

FIBER = [
    ('''#include "psx_fiber.h"

#if defined(_WIN32)''',
     '''#include "psx_fiber.h"

/* ''' + MARCA + ''': the App Container exports neither CreateFiber nor ConvertThreadToFiber,
 * only CreateFiberEx and ConvertThreadToFiberEx. This block is the console's; the one below is the
 * desktop's. */
#if defined(_WIN32) && defined(WINAPI_FAMILY) && WINAPI_FAMILY == WINAPI_FAMILY_APP

#define WIN32_LEAN_AND_MEAN
#include <windows.h>

psx_fiber_t psx_fiber_convert_thread(void)
{
    void* fiber = ConvertThreadToFiberEx(NULL, FIBER_FLAG_FLOAT_SWITCH);
    if (!fiber && GetLastError() == ERROR_ALREADY_FIBER)
        fiber = GetCurrentFiber();
    return (psx_fiber_t)fiber;
}

psx_fiber_t psx_fiber_current(void)
{
    return (psx_fiber_t)GetCurrentFiber();
}

psx_fiber_t psx_fiber_create(size_t stack_size, psx_fiber_entry entry, void* arg)
{
    return (psx_fiber_t)CreateFiberEx((SIZE_T)stack_size, 0,
                                      FIBER_FLAG_FLOAT_SWITCH,
                                      (LPFIBER_START_ROUTINE)entry, arg);
}

void psx_fiber_switch(psx_fiber_t target)
{
    if (target) SwitchToFiber((LPVOID)target);
}

void psx_fiber_destroy(psx_fiber_t fiber)
{
    if (fiber) DeleteFiber((LPVOID)fiber);
}

#elif defined(_WIN32)'''),
]

LOBBY = [
    ('''    psx_lobby_set_mod_offer_builder(&PSXRecompV4::mod_runtime_netplay_offer_json);''',
     '''#if !defined(PSX_UWP)   /* ''' + MARCA + ''': with netplay off, psx_lobby_client.c is not
                         * compiled, but this call carries no guard and leaves the symbol unresolved
                         * (LNK2019 in SDL_main). There is no netplay on a console. */
    psx_lobby_set_mod_offer_builder(&PSXRecompV4::mod_runtime_netplay_offer_json);
#endif'''),
]


def main():
    raiz = parchear.raiz()
    escritos = parchear.aplicar_varios([
        (parchear.runtime(raiz, 'runtime.cmake'), CMAKE),
        (parchear.runtime(raiz, 'src', 'crash_trace.c'), CRASH),
        (parchear.runtime(raiz, 'src', 'freeze_heartbeat.c'), HEARTBEAT),
        (parchear.runtime(raiz, 'src', 'autocompile.c'), AUTOCOMPILE),
        (parchear.runtime(raiz, 'src', 'psx_fiber.c'), FIBER),
        (parchear.runtime(raiz, 'src', 'main.cpp'), LOBBY),
    ], MARCA)
    parchear.informe('los cinco arreglos del framework: ' + ', '.join(escritos) if escritos else None,
                     nada='los cinco arreglos del framework ya estaban')


if __name__ == '__main__':
    main()
