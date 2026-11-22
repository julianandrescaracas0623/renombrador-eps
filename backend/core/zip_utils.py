"""Utilidades compartidas para empaquetar directorios temporales en archivos ZIP."""

import zipfile
from pathlib import Path


def zip_dir_a_archivo(directorio: Path, destino: Path) -> None:
    """Escribe el ZIP directo a disco: con lotes de varios GB no cabe en memoria."""
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
        for archivo in directorio.rglob("*"):
            if archivo.is_file():
                zf.write(archivo, arcname=archivo.relative_to(directorio))
