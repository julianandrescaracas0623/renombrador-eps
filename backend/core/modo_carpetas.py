"""Modo de salida 'carpetas' (SOS): un solo ZIP con tres carpetas planas.

soportes/  -> todos los PDF renombrados de todas las facturas.
rips/      -> los JSON de RIPS sin cambios.
cuv/       -> los JSON/TXT de CUV (archivos CUV_*) sin cambios. Los XML se omiten.

La cantidad de soportes por factura varía (unas traen autorización sin orden, otras las
dos), así que no se exige un conjunto fijo: se reporta cuántos trae cada factura. Lo único
que se avisa como faltante es lo obligatorio: la factura (FEV), el RIPS y el CUV.
"""

import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import BinaryIO

from .modo_soporte_rips import ZipInvalido, _carpeta_factura, _resolver_duplicado
from .prefijos import detectar_omitir_epi, ordenar_prefijos, renombrar_stem
from .zip_utils import zip_dir_a_archivo

EXTENSIONES_RIPS = (".json", ".txt")


def _volcar(
    origen: BinaryIO,
    prefijos_ordenados: list[tuple[str, str]],
    trabajo: Path,
    soportes_dir: Path,
    rips_dir: Path,
    cuv_dir: Path,
    usados_soportes: set[str],
    usados_rips: set[str],
    usados_cuv: set[str],
    facturas: dict[str, dict],
) -> dict:
    with zipfile.ZipFile(origen) as z:
        extraido = Path(tempfile.mkdtemp(dir=trabajo))
        z.extractall(extraido)

    archivos = [f for f in extraido.rglob("*") if f.is_file()]
    pdfs = [f for f in archivos if f.suffix.lower() == ".pdf"]
    omitir_epi = detectar_omitir_epi([pdf.stem for pdf in pdfs])
    prefijos = [origen for origen, _ in prefijos_ordenados]

    renombrados = 0
    conflictos = 0
    xml_omitidos = 0
    soportes_count = 0
    rips_count = 0
    cuv_count = 0

    for archivo in archivos:
        ext = archivo.suffix.lower()
        stem = archivo.stem
        factura = _carpeta_factura(archivo, extraido, prefijos)

        if ext == ".pdf":
            nuevo_stem = renombrar_stem(stem, prefijos_ordenados, omitir_epi)
            nuevo_nombre = f"{nuevo_stem}{archivo.suffix}"

            if nuevo_nombre != archivo.name:
                renombrados += 1

            nuevo_nombre, es_duplicado = _resolver_duplicado(
                "", nuevo_nombre, nuevo_stem, archivo.suffix, usados_soportes
            )
            if es_duplicado:
                conflictos += 1

            usados_soportes.add(f"/{nuevo_nombre}")
            shutil.copy2(archivo, soportes_dir / nuevo_nombre)
            soportes_count += 1

            info = facturas.setdefault(factura, {"soportes": 0, "tipos": set(), "rips": 0, "cuv": 0})
            info["soportes"] += 1
            info["tipos"].add(nuevo_stem.split("_", 1)[0].upper())

        elif ext in EXTENSIONES_RIPS:
            es_cuv = stem[:4].lower() == "cuv_"
            destino_dir = cuv_dir if es_cuv else rips_dir
            usados = usados_cuv if es_cuv else usados_rips

            nuevo_nombre, es_duplicado = _resolver_duplicado(
                "", archivo.name, stem, archivo.suffix, usados
            )
            if es_duplicado:
                conflictos += 1

            usados.add(f"/{nuevo_nombre}")
            shutil.copy2(archivo, destino_dir / nuevo_nombre)

            info = facturas.setdefault(factura, {"soportes": 0, "tipos": set(), "rips": 0, "cuv": 0})
            if es_cuv:
                info["cuv"] += 1
                cuv_count += 1
            else:
                info["rips"] += 1
                rips_count += 1

        elif ext == ".xml":
            xml_omitidos += 1

    shutil.rmtree(extraido, ignore_errors=True)

    return {
        "pdfs_totales": len(pdfs),
        "pdfs_renombrados": renombrados,
        "epi_omitidos": omitir_epi,
        "conflictos_duplicados": conflictos,
        "soporte_archivos": soportes_count,
        "rips_archivos": rips_count,
        "cuv_archivos": cuv_count,
        "xml_omitidos": xml_omitidos,
    }


def _avisos(facturas: dict[str, dict]) -> dict:
    return {
        "facturas_sin_fev": sorted(f for f, i in facturas.items() if i["soportes"] and "FEV" not in i["tipos"]),
        "facturas_sin_rips": sorted(f for f, i in facturas.items() if i["soportes"] and not i["rips"]),
        "facturas_sin_cuv": sorted(f for f, i in facturas.items() if not i["cuv"]),
        "facturas_sin_soportes": sorted(f for f, i in facturas.items() if not i["soportes"]),
    }


def procesar(entradas: list[tuple[str, BinaryIO]], mapeo: dict[str, str], destino: Path) -> dict:
    """Junta todos los ZIP subidos en un solo ZIP (destino) con soportes/, rips/ y cuv/."""
    prefijos_ordenados = ordenar_prefijos(mapeo)
    resumenes = []
    facturas: dict[str, dict] = {}

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        salida = tmp_path / "salida"
        soportes_dir = salida / "soportes"
        rips_dir = salida / "rips"
        cuv_dir = salida / "cuv"
        trabajo = tmp_path / "_extraido"
        soportes_dir.mkdir(parents=True)
        rips_dir.mkdir()
        cuv_dir.mkdir()
        trabajo.mkdir()

        usados_soportes: set[str] = set()
        usados_rips: set[str] = set()
        usados_cuv: set[str] = set()

        for nombre_archivo, origen in entradas:
            try:
                resumen = _volcar(
                    origen,
                    prefijos_ordenados,
                    trabajo,
                    soportes_dir,
                    rips_dir,
                    cuv_dir,
                    usados_soportes,
                    usados_rips,
                    usados_cuv,
                    facturas,
                )
            except zipfile.BadZipFile as error:
                raise ZipInvalido(nombre_archivo) from error

            resumenes.append({"archivo": nombre_archivo, **resumen})

        zip_dir_a_archivo(salida, destino)

    avisos = _avisos(facturas)
    # Los avisos son del lote completo (un RIPS puede venir en otro ZIP que sus soportes);
    # van en el primer resumen para que el frontend los muestre una sola vez.
    resumenes[0].update(avisos)
    resumenes[0]["facturas_totales"] = len(facturas)
    resumenes[0]["soportes_por_factura"] = {f: i["soportes"] for f, i in sorted(facturas.items())}

    return {"resumenes": resumenes}
