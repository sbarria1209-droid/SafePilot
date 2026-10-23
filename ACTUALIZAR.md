# Publicar una nueva versión

La publicación es manual y queda bajo el control del propietario de la cuenta. No hay flujos automáticos ni solicitudes de incorporación (Pull Requests) creadas por esta configuración.

1. Prepara y prueba el nuevo instalador en Windows.
2. Abre https://github.com/sbarria1209-droid/SafePilot/releases y pulsa **Draft a new release**.
3. Crea una etiqueta nueva, por ejemplo `v6.14`, con destino `main`.
4. Escribe el título y los cambios de esa versión.
5. Adjunta el nuevo archivo `_Instalador.exe` y su `SHA256.txt` en el recuadro de archivos de la release. Espera hasta que finalice la carga.
6. Marca **Set as latest release** y publica con **Publish release**. No marques **pre-release** para una entrega final.
7. Abre el enlace de descarga en una ventana privada para comprobar el acceso público y el tamaño del archivo.

Comparte siempre este enlace:

https://github.com/sbarria1209-droid/SafePilot/releases/latest

No cambia cuando se publica una nueva versión como Latest. Las versiones anteriores siguen disponibles en Releases. Publicar otra release no actualiza automáticamente las instalaciones existentes: el destinatario descarga y ejecuta el nuevo instalador.

## Comprobar la integridad del instalador

Para obtener el SHA-256 en PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\ruta\SafePilot_6.14_Instalador.exe'
```

Guarda el resultado y el nombre del archivo en `SHA256.txt`, y adjúntalo junto al instalador.

El instalador se adjunta en **Releases**, no en la lista de archivos del repositorio. GitHub admite archivos de release de menos de 2 GiB cada uno. Si una versión futura supera ese límite, habrá que preparar otro formato de entrega antes de publicarla.

Documentación oficial: https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository

Si más adelante incorporas el código fuente y quieres usar Pull Requests, puedes crearlas y revisarlas manualmente. No son necesarias para adjuntar un instalador en Releases.
