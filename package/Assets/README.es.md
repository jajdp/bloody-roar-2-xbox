# Aquí van tus mosaicos del paquete

*(English: [README.md](README.md))*

Esta carpeta está **vacía a propósito**. Los mosaicos del port de verdad se recortaron del arte del
propio juego, que es de Hudson Soft, así que aquí no se distribuyen: ver
[`../../NOTICE.es.md`](../../NOTICE.es.md).

Los nombres y las medidas exactas están en [`../../docs/ASSETS.es.md`](../../docs/ASSETS.es.md).
Imágenes de un color plano con las dimensiones correctas sirven: la consola solo necesita que existan y
que tengan la forma correcta.

`tools/empaquetar-uwp.ps1` averigua qué PNG nombra el manifiesto y se detiene antes de hacer nada si
falta alguno, diciendo cuál. El `.gitignore` deja fuera del repositorio los `*.png` de esta carpeta, así
que lo que pongas aquí no se subirá por descuido.
