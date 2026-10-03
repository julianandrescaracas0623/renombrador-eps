"""Modo de salida 'soporte_rips': puerto de RENOMBRADOR-2.0.ipynb (lógica de FOMAG).

Separa los archivos de todos los ZIP subidos en dos paquetes, tal como exige la
radicación en Horus (ver GUIA CUENTAS MEDICAS Y RIPS.pdf): los PDF renombrados van a
Sop.zip y los JSON/XML (RIPS, CUV, factura) van sin cambios a Rips.zip. Dentro de cada
paquete hay una carpeta por factura (SI30230) con sus archivos sueltos.
"""

import io
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from .prefijos import detectar_omitir_epi, ordenar_prefijos, renombrar_stem
from .zip_utils import zip_dir_a_bytes

_SUFIJO_CARPETA = re.compile(r"[\s_-]*(?:soportes?|rips?)$", re.IGNORECASE)


class ZipInvalido(Exception):
    def __init__(self, archivo: str):
        super().__init__(archivo)
        self.archivo = archivo


def _quitar_sufijo_carpeta(nombre: str) -> str:
    """Quita un sufijo final rip/rips/soporte/soportes: 'SI30230_rip' pasa a 'SI30230'."""
    limpio = _SUFIJO_CARPETA.sub("", nombre).strip()
    return limpio or nombre


def _id_factura_en_nombre(nombre: str, prefijos: list[str]) -> str | None:
    """Busca prefijo + dígitos en cualquier parte: CRC_900472731_SI30230 pasa a SI30230."""
    for prefijo in prefijos:
        patron = rf"(?:^|[^A-Za-z]){re.escape(prefijo)}(\d+)"
        encontrado = re.search(patron, nombre, re.IGNORECASE)
        if encontrado:
            return f"{prefijo}{encontrado.group(1)}"

    return None


def _carpeta_factura(archivo: Path, raiz: Path, prefijos: list[str]) -> str:
    """El id de la factura, igual para todos sus archivos. Las subcarpetas no se copian."""
    ancestros: list[Path] = []
    actual = archivo.parent
    while actual != raiz and actual.parent != actual:
        ancestros.append(actual)
        actual = actual.parent

    for carpeta in ancestros:
        identificado = _id_factura_en_nombre(carpeta.name, prefijos)
        if identificado:
            return identificado

    identificado = _id_factura_en_nombre(archivo.stem, prefijos)
    if identificado:
        return identificado

    for carpeta in ancestros:
        if _quitar_sufijo_carpeta(carpeta.name) != carpeta.name:
            return _quitar_sufijo_carpeta(carpeta.name)

    stem = archivo.stem[4:] if archivo.stem[:4].lower() == "cuv_" else archivo.stem
    return _quitar_sufijo_carpeta(stem) or archivo.stem


def _resolver_duplicado(
    carpeta: str,
    nuevo_nombre: str,
    stem: str,
    suffix: str,
    usados: set[str],
) -> tuple[str, bool]:
    clave = f"{carpeta}/{nuevo_nombre}"
    if clave not in usados:
        return nuevo_nombre, False

    contador = 1
    while f"{carpeta}/{stem}_DUPLICADO{contador}{suffix}" in usados:
        contador += 1

    return f"{stem}_DUPLICADO{contador}{suffix}", True


def _volcar(
    zip_bytes: bytes,
    prefijos_ordenados: list[tuple[str, str]],
    trabajo: Path,
    soporte_dir: Path,
    rips_dir: Path,
    usados_sop: set[str],
    usados_rips: set[str],
) -> dict:
    """Copia los archivos de un ZIP a las carpetas compartidas de Sop y Rips."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        extraido = Path(tempfile.mkdtemp(dir=trabajo))
        z.extractall(extraido)

    archivos = [f for f in extraido.rglob("*") if f.is_file()]

    pdfs = [f for f in archivos if f.suffix.lower() == ".pdf"]
    omitir_epi = detectar_omitir_epi([pdf.stem for pdf in pdfs])
    prefijos = [origen for origen, _ in prefijos_ordenados]

    renombrados = 0
    conflictos = 0
    soporte_count = 0
    rips_count = 0
    facturas_ids: set[str] = set()
    facturas_con_cuv: set[str] = set()

    for archivo in archivos:
        nombre = archivo.name
        stem = archivo.stem
        ext = archivo.suffix.lower()
        carpeta = _carpeta_factura(archivo, extraido, prefijos)

        if ext == ".pdf":
            nuevo_stem = renombrar_stem(stem, prefijos_ordenados, omitir_epi)
            nuevo_nombre = f"{nuevo_stem}{archivo.suffix}"

            if nuevo_nombre != nombre:
                renombrados += 1

            nuevo_nombre, es_duplicado = _resolver_duplicado(
                carpeta, nuevo_nombre, nuevo_stem, archivo.suffix, usados_sop
            )
            if es_duplicado:
                conflictos += 1

            usados_sop.add(f"{carpeta}/{nuevo_nombre}")
            destino = soporte_dir / carpeta
            destino.mkdir(parents=True, exist_ok=True)
            shutil.copy2(archivo, destino / nuevo_nombre)
            soporte_count += 1

        elif ext in (".json", ".xml"):
            nuevo_nombre, es_duplicado = _resolver_duplicado(
                carpeta, nombre, stem, archivo.suffix, usados_rips
            )
            if es_duplicado:
                conflictos += 1

            usados_rips.add(f"{carpeta}/{nuevo_nombre}")
            destino = rips_dir / carpeta
            destino.mkdir(parents=True, exist_ok=True)
            shutil.copy2(archivo, destino / nuevo_nombre)
            rips_count += 1

            facturas_ids.add(carpeta)
            if stem[:4].lower() == "cuv_":
                facturas_con_cuv.add(carpeta)

    shutil.rmtree(extraido, ignore_errors=True)

    return {
        "pdfs_totales": len(pdfs),
        "pdfs_renombrados": renombrados,
        "epi_omitidos": omitir_epi,
        "conflictos_duplicados": conflictos,
        "soporte_archivos": soporte_count,
        "rips_archivos": rips_count,
        "facturas_sin_cuv": sorted(facturas_ids - facturas_con_cuv),
    }


def procesar(entradas: list[tuple[str, bytes]], mapeo: dict[str, str]) -> dict:
    """Junta todos los ZIP subidos en un solo Sop.zip y un solo Rips.zip."""
    prefijos_ordenados = ordenar_prefijos(mapeo)
    resumenes = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        soporte_dir = tmp_path / "Sop"
        rips_dir = tmp_path / "Rips"
        trabajo = tmp_path / "_extraido"
        soporte_dir.mkdir()
        rips_dir.mkdir()
        trabajo.mkdir()

        usados_sop: set[str] = set()
        usados_rips: set[str] = set()

        for nombre_archivo, zip_bytes in entradas:
            try:
                resumen = _volcar(
                    zip_bytes,
                    prefijos_ordenados,
                    trabajo,
                    soporte_dir,
                    rips_dir,
                    usados_sop,
                    usados_rips,
                )
            except zipfile.BadZipFile as error:
                raise ZipInvalido(nombre_archivo) from error

            resumenes.append({"archivo": nombre_archivo, **resumen})

        soporte_bytes = zip_dir_a_bytes(soporte_dir)
        rips_bytes = zip_dir_a_bytes(rips_dir)

    return {"soporte": soporte_bytes, "rips": rips_bytes, "resumenes": resumenes}
