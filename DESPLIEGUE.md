# Despliegue en PythonAnywhere

Flask (`backend/app.py`) sirve la API y el frontend ya compilado en `frontend/dist`. En el plan gratuito el servidor no tiene Node: el build se genera en la PC y se sube con el repositorio. La plantilla del WSGI está en `backend/wsgi_pythonanywhere.py`; el archivo que ejecuta PythonAnywhere es el de la pestaña Web.

Repositorio: `https://github.com/julianandrescaracas0623/renombrador-eps.git`.

En los comandos, sustituye `TUUSUARIO` por tu usuario de PythonAnywhere. Esta guía usa la carpeta `renombrador-eps` (el nombre que deja `git clone`) y el virtualenv `renombrador`.

## Actualizar un sitio que ya existe

El clone, el virtualenv, el WSGI y la web app se quedan como están. Este es el ciclo de cada cambio.

1. En la PC, si cambió la interfaz, genera el build:

```bash
cd frontend
npm install
npm run build
```

Eso actualiza `frontend/dist` (`index.html` y la carpeta `assets` con los nombres con hash). Hay que incluir ese build en el commit: el `.gitignore` lo deja versionado a propósito.

2. Haz commit y push de la rama que está en el servidor (`Develop` o `inicio`).

3. En una consola Bash de PythonAnywhere:

```bash
cd ~/renombrador-eps
git pull
```

4. Solo si cambió `backend/requirements.txt`:

```bash
workon renombrador
pip install -r ~/renombrador-eps/backend/requirements.txt
```

5. En la pestaña **Web**, pulsa **Reload**.

Sin el Reload, el sitio sigue con el código anterior. Volver a clonar o a crear la web app solo hace falta si borraste la app, el entorno virtual o la carpeta del proyecto en el servidor.

## Primera instalación

1. Abre una consola **Bash** (pestaña Consoles) y clona la rama que quieras publicar:

```bash
cd ~
git clone https://github.com/julianandrescaracas0623/renombrador-eps.git
cd renombrador-eps
git checkout Develop
```

Si el repositorio es privado, GitHub pide un token de acceso personal.

2. Crea el virtualenv con la misma versión de Python que vas a elegir en la web app. Anota esa versión en la pestaña Web (por ejemplo 3.12) y úsala aquí:

```bash
mkvirtualenv renombrador --python=/usr/bin/python3.12
pip install -r ~/renombrador-eps/backend/requirements.txt
```

El prompt debe quedar `(renombrador)$`. Hoy el único paquete es `Flask==3.0.3`.

3. En la pestaña **Web**, pulsa **Add a new web app**.

- Dominio: `TUUSUARIO.pythonanywhere.com` (en el plan gratuito no hay otro).
- Tipo: **Manual configuration**.
- Python: la misma versión del paso anterior.

4. En la sección **Virtualenv**, escribe `renombrador` y confirma. Debe resolverse a `/home/TUUSUARIO/.virtualenvs/renombrador`.

5. Abre el enlace **WSGI configuration file** (queda en `/var/www/TUUSUARIO_pythonanywhere_com_wsgi.py`). Sustituye el ejemplo por esto, con tu usuario real:

```python
import sys

path = "/home/TUUSUARIO/renombrador-eps/backend"
if path not in sys.path:
    sys.path.append(path)

from app import app as application
```

Esa ruta es obligatoria: `app.py` importa el paquete `core`, que vive dentro de `backend`, y busca el frontend en la carpeta hermana `frontend/dist`.

6. Deja vacía la sección **Static files**. Flask atiende `/`, `/assets/...` y `/api/...`. Si mapeas `/` a una carpeta, esas rutas dejan de llegar a la API.

7. Pulsa **Reload** y abre `https://TUUSUARIO.pythonanywhere.com`. La página debe cargar y, al elegir una EPS, responder `/api/eps`.

## Si la página falla

En la pestaña **Web**, abre **Error log**. También está en `/var/log/TUUSUARIO.pythonanywhere.com.error.log`.

| Síntoma | Qué revisar |
|---|---|
| `No module named 'app'` o `No module named 'core'` | La ruta del WSGI debe ser `/home/TUUSUARIO/renombrador-eps/backend`. |
| `No module named 'flask'` | El virtualenv de la pestaña Web debe ser `renombrador`, y el `pip install` debe hacerse con ese entorno activo. |
| Pantalla en blanco | En el servidor falta `frontend/dist/assets/`. El `index.html` apunta a archivos con hash; tienen que venir en el `git pull`. |
| El ZIP no descarga | El resultado vive en memoria 10 minutos. Un Reload, o esperar más de eso, lo borra. Hay que procesar otra vez. |

## Límites del plan gratuito

- Un solo proceso. El ZIP se guarda en la memoria del mismo proceso que atendió `/api/procesar` y después `/api/descargar` (`backend/core/jobs.py`, 10 minutos).
- Tope de subida de la app: 200 MB en total (`MAX_CONTENT_LENGTH` en `backend/app.py`).
- Cuota diaria de CPU. Varios ZIP grandes pueden agotarla.
- El Reload corta las descargas que aún no se hayan pedido.
