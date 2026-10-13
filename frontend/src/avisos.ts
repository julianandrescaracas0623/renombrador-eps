type CampoAviso =
  | 'facturas_sin_cuv'
  | 'facturas_sin_rips'
  | 'facturas_sin_fev'
  | 'facturas_sin_soportes'

export const AVISOS: { campo: CampoAviso; titulo: string; ayuda: string }[] = [
  {
    campo: 'facturas_sin_cuv',
    titulo: 'Facturas sin CUV en el RIPS',
    ayuda: 'Estas facturas no traían el archivo CUV dentro del ZIP subido. Revísalas antes de radicar.',
  },
  {
    campo: 'facturas_sin_rips',
    titulo: 'Facturas sin archivo RIPS',
    ayuda: 'Estas facturas tienen soportes pero no traían su JSON de RIPS.',
  },
  {
    campo: 'facturas_sin_fev',
    titulo: 'Facturas sin PDF de factura (FEV)',
    ayuda: 'Estas facturas no traían el PDF de la factura con detallado (FEV_).',
  },
  {
    campo: 'facturas_sin_soportes',
    titulo: 'Facturas con RIPS pero sin soportes',
    ayuda: 'Estas facturas traían RIPS o CUV, pero ningún PDF de soporte.',
  },
]
