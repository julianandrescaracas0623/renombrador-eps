# Referencia: pega este bloque (ajustando la ruta) en el archivo WSGI que
# PythonAnywhere genera automáticamente en la pestaña "Web" -> "WSGI configuration file".
#
# Ejemplo de ruta: /var/www/tuusuario_pythonanywhere_com_wsgi.py

import sys

path = "/home/tuusuario/renombrador/backend"
if path not in sys.path:
    sys.path.append(path)

from app import app as application  # noqa: E402
