"""Almacén en disco de resultados para descargar, con expiración simple.

Los ZIP se guardan en una carpeta temporal junto al backend para que el
historial del frontend pueda volver a descargarlos (incluso tras un Reload en
PythonAnywhere) sin necesitar base de datos ni Redis. Se borran solos al
expirar o cuando el total supera el límite de espacio, empezando por los más
antiguos.
"""

import json
import os
import re
import threading
import time
import uuid
from pathlib import Path

TTL_SEGUNDOS = 24 * 60 * 60
# Lotes de hasta 100 ZIP de 20 MB dan resultados de ~2 GB; caben unos 10 en el historial.
_MAX_BYTES_TOTALES = 20 * 1024 * 1024 * 1024
_CARPETA = Path(__file__).parent.parent / "resultados_tmp"
_ID_VALIDO = re.compile(r"^[0-9a-f]{32}$")
_lock = threading.Lock()


def _ruta_zip(job_id: str) -> Path:
    return _CARPETA / f"{job_id}.zip"


def _ruta_meta(job_id: str) -> Path:
    return _CARPETA / f"{job_id}.json"


def ruta_temporal() -> Path:
    """Archivo donde escribir un resultado en curso, en la misma carpeta (y disco) que los jobs."""
    _CARPETA.mkdir(exist_ok=True)
    return _CARPETA / f"{uuid.uuid4().hex}.part"


def crear_job(ruta_resultado: Path, nombre_archivo: str) -> str:
    """Registra un resultado ya escrito en disco (ver ruta_temporal) y lo mueve a su sitio."""
    job_id = uuid.uuid4().hex

    with _lock:
        _CARPETA.mkdir(exist_ok=True)
        os.replace(ruta_resultado, _ruta_zip(job_id))
        _ruta_meta(job_id).write_text(
            json.dumps({"nombre_archivo": nombre_archivo, "creado": time.time()}),
            encoding="utf-8",
        )
        _limpiar()

    return job_id


def obtener_job(job_id: str) -> dict | None:
    """Devuelve {'ruta', 'nombre_archivo', 'creado'} o None si no existe o expiró."""
    if not _ID_VALIDO.match(job_id):
        return None

    with _lock:
        _limpiar()
        meta = _leer_meta(job_id)

        if meta is None or not _ruta_zip(job_id).is_file():
            return None

        return {"ruta": _ruta_zip(job_id), **meta}


def eliminar_job(job_id: str) -> None:
    if not _ID_VALIDO.match(job_id):
        return

    with _lock:
        _borrar(job_id)


def _leer_meta(job_id: str) -> dict | None:
    try:
        return json.loads(_ruta_meta(job_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _borrar(job_id: str) -> None:
    _ruta_zip(job_id).unlink(missing_ok=True)
    _ruta_meta(job_id).unlink(missing_ok=True)


def _limpiar() -> None:
    if not _CARPETA.is_dir():
        return

    ahora = time.time()
    vigentes = []

    # Restos de procesos que se cortaron a mitad (reinicio, error) sin registrarse.
    for parcial in _CARPETA.glob("*.part"):
        try:
            if ahora - parcial.stat().st_mtime > TTL_SEGUNDOS:
                parcial.unlink(missing_ok=True)
        except OSError:
            pass

    for meta_path in _CARPETA.glob("*.json"):
        job_id = meta_path.stem
        meta = _leer_meta(job_id)
        zip_path = _ruta_zip(job_id)

        if meta is None or not zip_path.is_file() or ahora - meta["creado"] > TTL_SEGUNDOS:
            _borrar(job_id)
            continue

        vigentes.append((meta["creado"], job_id, zip_path.stat().st_size))

    # Si se pasa del límite de espacio, se descartan primero los más antiguos
    vigentes.sort()
    total = sum(tamano for _, _, tamano in vigentes)

    for _, job_id, tamano in vigentes:
        if total <= _MAX_BYTES_TOTALES:
            break
        _borrar(job_id)
        total -= tamano
