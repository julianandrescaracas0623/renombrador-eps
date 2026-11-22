# Despliegue en el VPS de Hostinger (Coolify)

El sitio está publicado en **https://renombrador.juliancaracas.dev**. También responde en `https://srv2182907.hstgr.cloud`, la dirección anterior.

El VPS es de Hostinger: Ubuntu 24.04, 2 CPU, 8 GB de RAM y 96 GB de disco. Se administra con **Coolify** desde **https://panel.juliancaracas.dev**.

Una petición pasa por esta cadena:

```
navegador ──HTTPS──> coolify-proxy (Traefik, :80/:443) ──> contenedor renombrador-eps (:8000, gunicorn + Flask)
```

- **Traefik** (`coolify-proxy`) recibe el tráfico, saca y renueva solo los certificados de Let's Encrypt y enruta cada dominio a su contenedor.
- El **contenedor** se construye con el `Dockerfile` de este repo. Corre gunicorn con 2 workers y 4 threads, y sirve la API y `frontend/dist`.
- **Coolify** clona el repo con una deploy key de solo lectura (`github-renombrador-eps`) desde la rama `inicio`.
- `backend/resultados_tmp` vive en el volumen persistente `zsdtfahrlrgroo5zulvm7fic-resultados`. Los ZIP del historial sobreviven a los redespliegues.

## Actualizar el sitio

1. En la PC, si cambió la interfaz, genera el build y súbelo en el commit:

```bash
cd frontend
npm install
npm run build
```

`frontend/dist` se versiona a propósito, así la imagen no necesita Node.

2. Haz commit y push a `Develop`, abre un PR y mergéalo en `inicio`.

3. En el panel, entra a **Projects → renombrador → production → renombrador-eps** y pulsa **Redeploy**. El despliegue tarda alrededor de un minuto y la versión anterior sigue en línea hasta que la nueva está lista.

## Dónde mirar

| Para | Dónde |
|---|---|
| Estado, logs y redesplegar | Panel → la app → **Logs** / **Deployments** |
| Resumen de todo el VPS | `mis-proyectos` en una terminal SSH |
| Logs del contenedor desde SSH | `docker logs -f $(docker ps -qf name=zsdtfahrlrgroo5zulvm7fic)` |
| Logs del proxy | `docker logs -f coolify-proxy` |

## Agregar otro proyecto

El registro DNS comodín `*.juliancaracas.dev` ya apunta al VPS. Para publicar otro proyecto:

1. Agrega un `Dockerfile` al repo.
2. Crea una deploy key en el panel (**Keys & Tokens → Private Keys**) y regístrala en GitHub: repo → **Settings → Deploy keys**.
3. En el panel: **Projects → + Add → + New → Private Repository (with Deploy Key)**.
4. Pon un dominio como `https://app2.juliancaracas.dev` y el puerto que exponga la app, y pulsa **Deploy**. El HTTPS es automático.

## Si la página falla

| Síntoma | Qué revisar |
|---|---|
| `404 page not found` (de Traefik) | El dominio de la app en Coolify no coincide con la URL, o el contenedor está detenido. |
| `502 / Bad Gateway` | El contenedor no arrancó. Revisa los logs del despliegue en el panel. |
| Certificado inválido | Revisa `docker logs coolify-proxy \| grep -i acme`. Normalmente lo resuelve reiniciar el proxy (`docker restart coolify-proxy`). |
| `413 Request Entity Too Large` | La subida pasa de 2,5 GB (`MAX_CONTENT_MB` en `backend/app.py`). |
| Coolify dice que el servidor no es alcanzable | Revisa que fail2ban no haya bloqueado su IP interna (`sudo fail2ban-client status sshd`). Las redes `10.0.0.0/16` están en `/etc/fail2ban/jail.d/docker-ignore.local`. |

## Volver a la instalación anterior (nginx + systemd)

La configuración previa sigue en el servidor, apagada: `/etc/nginx/sites-available/renombrador-eps` y `renombrador-eps.service` en el puerto 8001. Para volver a ella:

```bash
docker stop coolify-proxy
sudo systemctl enable --now renombrador-eps nginx
```

`backend/wsgi_pythonanywhere.py` queda como plantilla por si algún día se publica en PythonAnywhere.
