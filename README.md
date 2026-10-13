# Renombrador EPS

Herramienta web para organizar y renombrar los archivos de soporte que se necesitan para **radicar cuentas médicas ante las EPS**.

## El problema

Cada EPS pide los soportes de las facturas (PDF, RIPS en JSON y XML, CUV) con nombres y una organización específicos. Preparar eso a mano implica:

- Renombrar decenas o cientos de archivos uno por uno.
- Separar los soportes de los RIPS en paquetes distintos.
- Agrupar todo por factura.
- Descubrir tarde que a alguna factura le falta un archivo y que la radicación será rechazada.

Es un trabajo repetitivo, lento y propenso a errores de digitación.

## Qué hace

1. Se elige la EPS.
2. Se suben los archivos (uno o varios ZIP).
3. La herramienta los renombra y organiza según las reglas de esa EPS.
4. Se descarga el resultado listo para radicar.

Además avisa cuando detecta facturas incompletas (por ejemplo, sin su archivo CUV), para corregirlas antes de enviar.

## EPS disponibles

| EPS | Resultado |
| --- | --- |
| **SOS** | Un único ZIP con los archivos renombrados, conservando la estructura de carpetas. |
| **FOMAG** | Un ZIP con dos paquetes: `Sop.zip` (soportes en PDF) y `Rips.zip` (JSON y XML), con una carpeta por factura. |

Agregar una EPS nueva no requiere reescribir la herramienta: se define como una configuración.

## Uso

La herramienta está publicada en línea y se usa desde el navegador, sin instalar nada. Para la guía de despliegue, ver [DESPLIEGUE.md](DESPLIEGUE.md).
