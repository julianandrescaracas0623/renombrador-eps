"""Almacén en memoria de resultados pendientes de descarga, con expiración simple.

Suficiente para un plan free de un solo proceso (PythonAnywhere): no requiere
base de datos ni Redis, solo evita que la respuesta de /api/procesar tenga que
incluir el ZIP completo en el JSON de resumen.
"""

import threading
import time
import uuid

_TTL_SEGUNDOS = 600
_lock = threading.Lock()
_jobs: dict[str, dict] = {}


def crear_job(zip_bytes: bytes, nombre_archivo: str) -> str:
    job_id = uuid.uuid4().hex

    with _lock:
        _limpiar_expirados()
        _jobs[job_id] = {
            "bytes": zip_bytes,
            "nombre_archivo": nombre_archivo,
            "creado": time.time(),
        }

    return job_id


def obtener_job(job_id: str) -> dict | None:
    with _lock:
        _limpiar_expirados()
        return _jobs.get(job_id)


def eliminar_job(job_id: str) -> None:
    with _lock:
        _jobs.pop(job_id, None)


def _limpiar_expirados() -> None:
    ahora = time.time()
    expirados = [
        job_id
        for job_id, job in _jobs.items()
        if ahora - job["creado"] > _TTL_SEGUNDOS
    ]

    for job_id in expirados:
        _jobs.pop(job_id, None)
