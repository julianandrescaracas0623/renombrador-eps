# Despliegue en el VPS de Hostinger

El sitio está publicado en **https://srv2182907.hstgr.cloud**, un VPS de Hostinger con Ubuntu 24.04 y 2 CPU, 8 GB de RAM y 96 GB de disco.

Una petición pasa por esta cadena:

```
navegador ──HTTPS──> nginx (:80/:443) ──> gunicorn (127.0.0.1:8000) ──> Flask (backend/app.py)
```

- **nginx** recibe el tráfico público, maneja el certificado HTTPS y reenvía todo a gunicorn. Su configuración está en `/etc/nginx/sites-available/renombrador-eps`.
- **gunicorn** ejecuta la app Flask con 2 workers y 4 threads. Lo arranca el servicio systemd `renombrador-eps`, definido en `/etc/systemd/system/renombrador-eps.service`.
- **Flask** atiende `/api/...` y también sirve el frontend ya compilado desde `frontend/dist`.
- El código vive en `/home/julian/renombrador-eps`, en la rama `inicio`, con el virtualenv en `.venv/`.

## Actualizar el sitio

1. En la PC, si cambió la interfaz, genera el build y súbelo en el commit:

```bash
cd frontend
npm install
npm run build
```

`frontend/dist` se versiona a propósito, así el servidor no necesita Node.

2. Haz commit y push a la rama que está en el servidor (`inicio`).

3. En el VPS, conectado por SSH (`ssh julian@srv2182907.hstgr.cloud`):

```bash
cd ~/renombrador-eps
git pull
# solo si cambió backend/requirements.txt:
.venv/bin/pip install -r backend/requirements.txt
sudo systemctl restart renombrador-eps
```

4. Comprueba que el sitio responde:

```bash
systemctl status renombrador-eps --no-pager
curl -s https://srv2182907.hstgr.cloud/api/eps
```

Sin el `restart`, gunicorn sigue ejecutando el código anterior. Los ZIP generados no se pierden al reiniciar, porque se guardan en disco.

## Comandos útiles

| Para | Comando |
|---|---|
| Resumen de todo lo desplegado | `mis-proyectos` |
| Estado del servicio | `systemctl status renombrador-eps` |
| Reiniciar la app | `sudo systemctl restart renombrador-eps` |
| Logs de la app en vivo | `journalctl -u renombrador-eps -f` |
| Logs de nginx | `sudo tail -f /var/log/nginx/error.log` (o `access.log`) |
| Validar y recargar nginx | `sudo nginx -t && sudo systemctl reload nginx` |
| Ver certificados | `sudo certbot certificates` |

## HTTPS

El certificado es de Let's Encrypt y está emitido para `srv2182907.hstgr.cloud`, el hostname que Hostinger asigna al VPS. Caduca cada 90 días y lo renueva solo el timer `certbot.timer`, que puedes revisar con `systemctl list-timers certbot.timer`. Las peticiones por HTTP se redirigen a HTTPS.

Para usar un dominio propio:

1. En el DNS del dominio, crea un registro `A` que apunte a `76.13.165.71`.
2. Agrega el dominio a `server_name` en `/etc/nginx/sites-available/renombrador-eps`.
3. Ejecuta `sudo certbot --nginx -d tudominio.com`.

## Primera instalación (si hubiera que rehacer el servidor)

```bash
sudo apt install -y nginx certbot python3-certbot-nginx python3-venv git
cd ~ && git clone https://github.com/julianandrescaracas0623/renombrador-eps.git
cd renombrador-eps && git checkout inicio
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt gunicorn
```

`gunicorn` no está en `requirements.txt` porque solo hace falta en el servidor. Después de instalar los paquetes:

1. Crea `/etc/systemd/system/renombrador-eps.service`:

```ini
[Unit]
Description=Renombrador EPS (Flask + gunicorn)
After=network.target

[Service]
User=julian
Group=julian
WorkingDirectory=/home/julian/renombrador-eps/backend
ExecStart=/home/julian/renombrador-eps/.venv/bin/gunicorn --workers 2 --threads 4 --timeout 300 --bind 127.0.0.1:8000 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now renombrador-eps
```

2. Crea `/etc/nginx/sites-available/renombrador-eps`:

```nginx
server {
    listen 80;
    server_name srv2182907.hstgr.cloud;
    client_max_body_size 210M;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        proxy_request_buffering off;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/renombrador-eps /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable
sudo certbot --nginx -d srv2182907.hstgr.cloud --redirect
```

## Si la página falla

| Síntoma | Qué revisar |
|---|---|
| `502 Bad Gateway` | gunicorn está caído. Revisa `systemctl status renombrador-eps` y `journalctl -u renombrador-eps -n 50`. |
| `413 Request Entity Too Large` | La subida pasa de 200 MB (`MAX_CONTENT_LENGTH` en `backend/app.py`; nginx permite 210 MB). |
| `504 Gateway Timeout` | El proceso tardó más de 300 s. Sube `--timeout` en el servicio y `proxy_read_timeout` en nginx. |
| Pantalla en blanco | Falta `frontend/dist/assets/` en el servidor; el build tiene que venir en el `git pull`. |
| El ZIP no descarga | Los resultados viven en `backend/resultados_tmp/` durante 24 h, con un máximo de 300 MB en total (`backend/core/jobs.py`). Pasado ese tiempo hay que procesar otra vez. |
| Cambios que no aparecen | Faltó `sudo systemctl restart renombrador-eps` después del `git pull`. |

## Alternativa: PythonAnywhere

`backend/wsgi_pythonanywhere.py` sigue en el repositorio como plantilla por si algún día se publica allí. En ese caso, el archivo WSGI tiene que añadir `/home/USUARIO/renombrador-eps/backend` a `sys.path` y hacer `from app import app as application`.
