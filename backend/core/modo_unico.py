"""Modo de salida 'unico': puerto de RENOMBRADOR-1.0.ipynb (lógica de la EPS SOS).

Renombra los PDF dentro del ZIP según el mapeo de prefijos y conserva el resto de
archivos/carpetas tal como venían, devolviendo un único ZIP.
"""

import io
import tempfile
import zipfile
from pathlib import Path

from .prefijos import detectar_omitir_epi, ordenar_prefijos, renombrar_stem
from .zip_utils import zip_dir_a_bytes


def procesar(zip_bytes: bytes, mapeo: dict[str, str]) -> tuple[bytes, dict]:
    prefijos_ordenados = ordenar_prefijos(mapeo)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            z.extractall(tmp_path)

        pdfs = list(tmp_path.rglob("*.pdf"))
        omitir_epi = detectar_omitir_epi([pdf.stem for pdf in pdfs])

        renombrados = 0

        for pdf in pdfs:
            nuevo_stem = renombrar_stem(pdf.stem, prefijos_ordenados, omitir_epi)

            if nuevo_stem != pdf.stem:
                pdf.rename(pdf.with_name(f"{nuevo_stem}{pdf.suffix}"))
                renombrados += 1

        resultado = zip_dir_a_bytes(tmp_path)

    resumen = {
        "pdfs_totales": len(pdfs),
        "pdfs_renombrados": renombrados,
        "epi_omitidos": omitir_epi,
    }

    return resultado, resumen
