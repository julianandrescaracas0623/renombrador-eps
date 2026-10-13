import io
import zipfile
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from werkzeug.utils import secure_filename

from core import eps_config, jobs, modo_carpetas, modo_soporte_rips, modo_unico
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

    if eps.modo_salida == "soporte_rips":
        entradas = [
            (secure_filename(archivo.filename or "archivo.zip"), archivo.read())
            for archivo in archivos
        ]

        try:
            resultado = modo_soporte_rips.procesar(entradas, mapeo)
        except modo_soporte_rips.ZipInvalido as error:
            return jsonify({"error": f"'{error.archivo}' no es un ZIP válido."}), 400

        with zipfile.ZipFile(contenedor_buffer, "w", zipfile.ZIP_DEFLATED) as contenedor:
            contenedor.writestr("Sop.zip", resultado["soporte"])
            contenedor.writestr("Rips.zip", resultado["rips"])

        resumen_por_archivo = resultado["resumenes"]
    elif eps.modo_salida == "carpetas":
        entradas = [
            (secure_filename(archivo.filename or "archivo.zip"), archivo.read())
            for archivo in archivos
        ]

        try:
            resultado = modo_carpetas.procesar(entradas, mapeo)
        except modo_carpetas.ZipInvalido as error:
            return jsonify({"error": f"'{error.archivo}' no es un ZIP válido."}), 400

        contenedor_buffer.write(resultado["contenido"])
        resumen_por_archivo = resultado["resumenes"]
    elif eps.modo_salida == "unico":
        with zipfile.ZipFile(contenedor_buffer, "w", zipfile.ZIP_DEFLATED) as contenedor:
            for archivo in archivos:
                nombre_original = secure_filename(archivo.filename or "archivo.zip")
                base = Path(nombre_original).stem

                try:
                    resultado_bytes, resumen = modo_unico.procesar(archivo.read(), mapeo)
                except zipfile.BadZipFile:
                    return jsonify({"error": f"'{nombre_original}' no es un ZIP válido."}), 400

                contenedor.writestr(f"{base}.zip", resultado_bytes)
                resumen_por_archivo.append({"archivo": nombre_original, **resumen})
    else:
        return jsonify({"error": f"Modo de salida no soportado: {eps.modo_salida}"}), 500

    job_id = jobs.crear_job(contenedor_buffer.getvalue(), f"resultado_{eps.id}.zip")

    return jsonify(
        {
            "job_id": job_id,
            "eps": eps.nombre,
            "resumen": resumen_por_archivo,
            "expira_en": jobs.TTL_SEGUNDOS,
        }
    )


@app.get("/api/descargar/<job_id>")
def descargar(job_id: str):
    job = jobs.obtener_job(job_id)

    if job is None:
        return jsonify({"error": "El resultado ya no está disponible, procesa de nuevo."}), 404

    return send_file(
        job["ruta"],
        mimetype="application/zip",
        as_attachment=True,
        download_name=job["nombre_archivo"],
    )


@app.delete("/api/resultados/<job_id>")
def eliminar_resultado(job_id: str):
    jobs.eliminar_job(job_id)
    return "", 204


@app.get("/")
@app.get("/<path:ruta>")
def frontend(ruta: str = ""):
    archivo = FRONTEND_DIST / ruta

    if ruta and archivo.is_file():
        return send_from_directory(FRONTEND_DIST, ruta)

    return send_from_directory(FRONTEND_DIST, "index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
