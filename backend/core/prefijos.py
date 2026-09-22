"""Utilidades de mapeo de prefijos, replicando la lógica de los notebooks originales."""


def ordenar_prefijos(mapeo: dict[str, str]) -> list[tuple[str, str]]:
    """Prefijos más largos primero, para que 'SNFE' no sea capturado por 'SI', etc."""
    return sorted(mapeo.items(), key=lambda item: len(item[0]), reverse=True)


def parsear_mapeo(texto: str) -> dict[str, str]:
    """Convierte líneas 'ORIGEN=DESTINO' en un dict. Ignora vacías y '# comentarios'."""
    mapeo: dict[str, str] = {}

    for linea in texto.splitlines():
        linea = linea.strip()

        if not linea or linea.startswith("#"):
            continue

        if "=" not in linea:
            continue

        origen, destino = linea.split("=", 1)
        origen = origen.strip()
        destino = destino.strip()

        if origen and destino:
            mapeo[origen] = destino

    return mapeo


def renombrar_stem(stem: str, prefijos_ordenados: list[tuple[str, str]], omitir_epi: bool) -> str:
    """Aplica el reemplazo de prefijo a un nombre de archivo sin extensión."""
    if omitir_epi and stem.startswith("EPI"):
        return stem

    for origen, destino in prefijos_ordenados:
        if stem.startswith(origen):
            return f"{destino}{stem[len(origen):]}"

    return stem


def detectar_omitir_epi(stems: list[str]) -> bool:
    """Regla de ambos notebooks: si coexisten EPI y HEV en el mismo ZIP, no se renombra EPI."""
    tiene_epi = any(stem.startswith("EPI") for stem in stems)
    tiene_hev = any(stem.startswith("HEV") for stem in stems)
    return tiene_epi and tiene_hev
