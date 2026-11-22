import tempfile
import zipfile
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from werkzeug.utils import secure_filename

from core import eps_config, jobs, modo_carpetas, modo_soporte_rips, modo_unico
from core.prefijos import parsear_mapeo

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

app = Flask(__name__, static_folder=None)

# 100 ZIP de hasta 20 MB = 2 GB, más margen.
MAX_CONTENT_MB = 2500
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

    # Werkzeug ya guardó cada archivo subido en un temporal en disco; se procesan desde
    # ahí, uno a uno, y el resultado se escribe directo a disco. Así un lote de ~2 GB
    # no pasa nunca entero por la memoria.
    entradas = [
        (secure_filename(archivo.filename or "archivo.zip"), archivo.stream)
        for archivo in archivos
    ]
    salida = jobs.ruta_temporal()

    try:
        resumen_por_archivo = _procesar_a_disco(eps.modo_salida, entradas, mapeo, salida)
    except (modo_soporte_rips.ZipInvalido, modo_carpetas.ZipInvalido) as error:
        salida.unlink(missing_ok=True)
        return jsonify({"error": f"'{error.archivo}' no es un ZIP válido."}), 400
    except ValueError as error:
        salida.unlink(missing_ok=True)
        return jsonify({"error": str(error)}), 500
    except BaseException:
        salida.unlink(missing_ok=True)
        raise

    job_id = jobs.crear_job(salida, f"resultado_{eps.id}.zip")

    return jsonify(
        {
            "job_id": job_id,
            "eps": eps.nombre,
            "resumen": resumen_por_archivo,
            "expira_en": jobs.TTL_SEGUNDOS,
        }
    )


def _procesar_a_disco(modo_salida: str, entradas: list, mapeo: dict[str, str], salida: Path) -> list:
    if modo_salida == "soporte_rips":
        with tempfile.TemporaryDirectory(dir=salida.parent) as tmp:
            soporte = Path(tmp) / "Sop.zip"
            rips = Path(tmp) / "Rips.zip"
            resultado = modo_soporte_rips.procesar(entradas, mapeo, soporte, rips)

            with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as contenedor:
                contenedor.write(soporte, "Sop.zip")
                contenedor.write(rips, "Rips.zip")

        return resultado["resumenes"]

    if modo_salida == "carpetas":
        return modo_carpetas.procesar(entradas, mapeo, salida)["resumenes"]

    if modo_salida == "unico":
        resumenes = []

        with tempfile.TemporaryDirectory(dir=salida.parent) as tmp, zipfile.ZipFile(
            salida, "w", zipfile.ZIP_DEFLATED
        ) as contenedor:
            for nombre_original, origen in entradas:
                parcial = Path(tmp) / "parcial.zip"

                try:
                    resumen = modo_unico.procesar(origen, mapeo, parcial)
                except zipfile.BadZipFile as error:
                    raise modo_carpetas.ZipInvalido(nombre_original) from error

                contenedor.write(parcial, f"{Path(nombre_original).stem}.zip")
                parcial.unlink()
                resumenes.append({"archivo": nombre_original, **resumen})

        return resumenes

    raise ValueError(f"Modo de salida no soportado: {modo_salida}")


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
