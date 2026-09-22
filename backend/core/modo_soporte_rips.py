"""Modo de salida 'soporte_rips': puerto de RENOMBRADOR-2.0.ipynb (lógica de FOMAG).

Separa los archivos del ZIP de entrada en dos paquetes, tal como exige la radicación
en Horus (ver GUIA CUENTAS MEDICAS Y RIPS.pdf): los PDF renombrados van a SOPORTE,
y los JSON/XML (RIPS, CUV, factura) van sin cambios a RIPS.
"""

import io
import shutil
import tempfile
import zipfile
from pathlib import Path

from .prefijos import detectar_omitir_epi, ordenar_prefijos, renombrar_stem
from .zip_utils import zip_dir_a_bytes


def _id_factura(stem: str) -> tuple[str, bool]:
    """Agrupa RIPS/CUV/XML de una misma factura quitando el prefijo 'CUV_'."""
    if stem[:4].lower() == "cuv_":
        return stem[4:], True
    return stem, False


def procesar(zip_bytes: bytes, mapeo: dict[str, str]) -> dict:
    prefijos_ordenados = ordenar_prefijos(mapeo)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        soporte_dir = tmp_path / "SOPORTE"
        rips_dir = tmp_path / "RIPS"
        soporte_dir.mkdir()
        rips_dir.mkdir()

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            extraido = tmp_path / "_extraido"
            extraido.mkdir()
            z.extractall(extraido)

        archivos = [f for f in extraido.rglob("*") if f.is_file()]

        pdfs = [f for f in archivos if f.suffix.lower() == ".pdf"]
        omitir_epi = detectar_omitir_epi([pdf.stem for pdf in pdfs])

        renombrados = 0
        conflictos = 0
        soporte_count = 0
        rips_count = 0
        nombres_usados: set[str] = set()
        facturas_ids: set[str] = set()
        facturas_con_cuv: set[str] = set()

        for archivo in archivos:
            nombre = archivo.name
            stem = archivo.stem
            ext = archivo.suffix.lower()

            if ext == ".pdf":
                nuevo_stem = renombrar_stem(stem, prefijos_ordenados, omitir_epi)
                nuevo_nombre = f"{nuevo_stem}{archivo.suffix}"

                if nuevo_nombre != nombre:
                    renombrados += 1

                if nuevo_nombre in nombres_usados:
                    conflictos += 1
                    base = nuevo_stem
                    contador = 1

                    while f"{base}_DUPLICADO{contador}{archivo.suffix}" in nombres_usados:
                        contador += 1

                    nuevo_nombre = f"{base}_DUPLICADO{contador}{archivo.suffix}"

                nombres_usados.add(nuevo_nombre)
                shutil.copy2(archivo, soporte_dir / nuevo_nombre)
                soporte_count += 1

            elif ext in (".json", ".xml"):
                shutil.copy2(archivo, rips_dir / nombre)
                rips_count += 1

                factura_id, es_cuv = _id_factura(stem)
                facturas_ids.add(factura_id)
                if es_cuv:
                    facturas_con_cuv.add(factura_id)

        soporte_bytes = zip_dir_a_bytes(soporte_dir)
        rips_bytes = zip_dir_a_bytes(rips_dir)

    facturas_sin_cuv = sorted(facturas_ids - facturas_con_cuv)

    resumen = {
        "pdfs_totales": len(pdfs),
        "pdfs_renombrados": renombrados,
        "epi_omitidos": omitir_epi,
        "conflictos_duplicados": conflictos,
        "soporte_archivos": soporte_count,
        "rips_archivos": rips_count,
        "facturas_sin_cuv": facturas_sin_cuv,
    }

    return {"soporte": soporte_bytes, "rips": rips_bytes, "resumen": resumen}
