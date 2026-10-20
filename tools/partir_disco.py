# Parte un archivo en trozos para subirlo por el Device Portal de la Xbox.
#
# Las subidas del portal pasan por D:\DevelopmentFiles, una partición de 5 GB que en una consola con
# algún juego instalado suele estar casi llena: la imagen de disco de este juego (527 MiB) responde
# HTTP 500 de una pieza. En partes de 150 MiB entra, y la entrada WinRT del port
# (src/SDL_winrt_main_NonXAML.cpp) las une en el primer arranque, una sola vez; las partes se quedan
# donde están, así que conviene borrarlas de la consola después.
#
# El SHA-1 que imprime al final es del archivo entero, para comprobar que lo unido es lo mismo que se
# partió.
#
# Uso: python partir_disco.py <archivo> <carpeta de salida> [MiB por parte, 150 por defecto]
import hashlib
import os
import sys

if len(sys.argv) < 3:
    sys.exit('uso: %s <archivo> <carpeta de salida> [MiB por parte]' % os.path.basename(sys.argv[0]))

ruta, salida = sys.argv[1], sys.argv[2]
tam = (int(sys.argv[3]) if len(sys.argv) > 3 else 150) * 1024 * 1024
os.makedirs(salida, exist_ok=True)
nombre = os.path.basename(ruta)
h = hashlib.sha1()
i = 0
with open(ruta, "rb") as f:
    while True:
        datos = f.read(tam)
        if not datos:
            break
        i += 1
        h.update(datos)
        destino = os.path.join(salida, f"{nombre}.parte{i}")
        tmp = destino + ".tmp"
        with open(tmp, "wb") as o:
            o.write(datos)
        os.replace(tmp, destino)
        print(f"{destino}: {len(datos)} bytes")
print(f"{i} partes; SHA-1 del total {h.hexdigest()}")
