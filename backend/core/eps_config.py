"""Registro de EPS soportadas. Agregar una EPS nueva = agregar una entrada aquí.

modo_salida:
  - "unico"         -> un solo ZIP renombrado (lógica de RENOMBRADOR-1.0.ipynb, hoy usada por SOS)
  - "soporte_rips"  -> separa PDF en Sop.zip y JSON/XML en Rips.zip,
                       cada factura en una carpeta con solo el número
                       (lógica de RENOMBRADOR-2.0.ipynb, hoy usada por FOMAG)
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EpsConfig:
    id: str
    nombre: str
    modo_salida: str
    mapeo_default: dict[str, str] = field(default_factory=dict)


EPS_DISPONIBLES: dict[str, EpsConfig] = {
    "sos": EpsConfig(
        id="sos",
        nombre="SOS",
        modo_salida="unico",
        mapeo_default={"SI": "FEV_900472731_SI"},
    ),
    "fomag": EpsConfig(
        id="fomag",
        nombre="FOMAG",
        modo_salida="soporte_rips",
        mapeo_default={"SI": "FEV_900472731_SI"},
    ),
}


def obtener_eps(eps_id: str) -> EpsConfig | None:
    return EPS_DISPONIBLES.get(eps_id)


def listar_eps() -> list[EpsConfig]:
    return list(EPS_DISPONIBLES.values())
