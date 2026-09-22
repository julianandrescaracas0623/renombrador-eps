import io
import zipfile
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from werkzeug.utils import secure_filename

from core import eps_config, jobs, modo_soporte_rips, modo_unico
from core.prefijos import parsear_mapeo

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

app = Flask(__name__, static_folder=None)

MAX_CONTENT_MB = 200
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_MB * 1024 * 1024


@app.errorhandler(413)
def archivo_demasiado_grande(_error):
    return jsonify({"error": f"El total subido supera el límite de {MAX_CONTENT_MB} MB."}), 413


@app.get("/api/eps")
def listar_eps():
    return jsonify(
        [
            {
                "id": eps.id,
                "nombre": eps.nombre,
                "modo_salida": eps.modo_salida,
                "mapeo_default": eps.mapeo_default,
            }
            for eps in eps_config.listar_eps()
        ]
    )


@app.post("/api/procesar")
def procesar():
    eps_id = request.form.get("eps_id", "")
    eps = eps_config.obtener_eps(eps_id)

    if eps is None:
        return jsonify({"error": f"EPS desconocida: {eps_id}"}), 400

    archivos = request.files.getlist("archivos")

    if not archivos:
        return jsonify({"error": "Debes subir al menos un archivo ZIP."}), 400

    mapeo_texto = request.form.get("mapeo", "")
    mapeo = parsear_mapeo(mapeo_texto) if mapeo_texto.strip() else dict(eps.mapeo_default)

    if not mapeo:
        return jsonify({"error": "El mapeo de prefijos no puede estar vacío."}), 400

    contenedor_buffer = io.BytesIO()
    resumen_por_archivo = []

    with zipfile.ZipFile(contenedor_buffer, "w", zipfile.ZIP_DEFLATED) as contenedor:
        for archivo in archivos:
            nombre_original = secure_filename(archivo.filename or "archivo.zip")
            base = Path(nombre_original).stem
            zip_bytes = archivo.read()

            try:
                if eps.modo_salida == "unico":
                    resultado_bytes, resumen = modo_unico.procesar(zip_bytes, mapeo)
                    contenedor.writestr(f"{base}.zip", resultado_bytes)
                elif eps.modo_salida == "soporte_rips":
                    resultado = modo_soporte_rips.procesar(zip_bytes, mapeo)
                    resumen = resultado["resumen"]
                    contenedor.writestr(f"{base}_SOPORTE.zip", resultado["soporte"])
                    contenedor.writestr(f"{base}_RIPS.zip", resultado["rips"])
                else:
                    return jsonify({"error": f"Modo de salida no soportado: {eps.modo_salida}"}), 500
            except zipfile.BadZipFile:
                return jsonify({"error": f"'{nombre_original}' no es un ZIP válido."}), 400

            resumen_por_archivo.append({"archivo": nombre_original, **resumen})

    job_id = jobs.crear_job(contenedor_buffer.getvalue(), f"resultado_{eps.id}.zip")

    return jsonify(
        {
            "job_id": job_id,
            "eps": eps.nombre,
            "resumen": resumen_por_archivo,
        }
    )


@app.get("/api/descargar/<job_id>")
def descargar(job_id: str):
    job = jobs.obtener_job(job_id)

    if job is None:
        return jsonify({"error": "El resultado ya no está disponible, procesa de nuevo."}), 404

    jobs.eliminar_job(job_id)

    return send_file(
        io.BytesIO(job["bytes"]),
        mimetype="application/zip",
        as_attachment=True,
        download_name=job["nombre_archivo"],
    )


@app.get("/")
@app.get("/<path:ruta>")
def frontend(ruta: str = ""):
    archivo = FRONTEND_DIST / ruta

    if ruta and archivo.is_file():
        return send_from_directory(FRONTEND_DIST, ruta)

    return send_from_directory(FRONTEND_DIST, "index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
