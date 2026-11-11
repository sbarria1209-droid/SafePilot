# MODIX HTTPS

Puente de solo lectura para la cámara USB y el monitor de capas de MODIX. Carpeta independiente del proyecto SafePilot.

Sin dependencias externas. Python 3.12 o superior. Inicio: `python modix-puente/bridge.py` desde la raíz del repositorio.

Variables: `MODIX_OWNER_TOKEN` (secreto de al menos 32 caracteres, configurado exclusivamente en Render), `PORT` (10000 por defecto), `MODIX_OUTPUT_LIMIT` (límite preventivo de transferencia por mes e instancia, 1 GB por defecto; se reinicia al reiniciarse el servidor).

Los datos permanecen en memoria, caducan tras 15 segundos sin publicar y se revocan al cerrar el acceso. No hay endpoints de control de impresora. La principal crea una clave nueva para el visor al compartir. No publiques las claves en GitHub.

Render Free puede suspenderse por inactividad o cuotas. La cámara remota reduce tamaño/calidad para ahorrar transferencia; la cámara local conserva su perfil.
