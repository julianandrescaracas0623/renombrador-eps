"""Utilidades compartidas para empaquetar directorios temporales en bytes de ZIP."""

import io
import zipfile
from pathlib import Path


def zip_dir_a_bytes(directorio: Path) -> bytes:
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for archivo in directorio.rglob("*"):
            if archivo.is_file():
                zf.write(archivo, arcname=archivo.relative_to(directorio))

    return buffer.getvalue()
