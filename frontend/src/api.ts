export interface EpsConfig {
  id: string
  nombre: string
  modo_salida: 'unico' | 'soporte_rips' | 'carpetas'
  mapeo_default: Record<string, string>
}

export interface ResumenArchivo {
  archivo: string
  pdfs_totales: number
  pdfs_renombrados: number
  epi_omitidos: boolean
  conflictos_duplicados?: number
  soporte_archivos?: number
  rips_archivos?: number
  facturas_sin_cuv?: string[]
  facturas_sin_rips?: string[]
  facturas_sin_fev?: string[]
  facturas_sin_soportes?: string[]
  facturas_totales?: number
  xml_omitidos?: number
  soportes_por_factura?: Record<string, number>
}

export interface ProcesarResponse {
  job_id: string
  eps: string
  resumen: ResumenArchivo[]
  expira_en: number
}

export interface ApiError {
  error: string
}

async function manejarError(res: Response): Promise<never> {
  let mensaje = `Error ${res.status}`

  try {
    const data = (await res.json()) as ApiError
    if (data.error) mensaje = data.error
  } catch {
    // respuesta sin cuerpo JSON, se conserva el mensaje genérico
  }

  throw new Error(mensaje)
}

export async function obtenerEps(): Promise<EpsConfig[]> {
  const res = await fetch('/api/eps')
  if (!res.ok) return manejarError(res)
  return res.json()
}

export async function procesarArchivos(
  epsId: string,
  mapeoTexto: string,
  archivos: File[],
): Promise<ProcesarResponse> {
  const form = new FormData()
  form.append('eps_id', epsId)
  form.append('mapeo', mapeoTexto)
  archivos.forEach((archivo) => form.append('archivos', archivo))

  const res = await fetch('/api/procesar', { method: 'POST', body: form })
  if (!res.ok) return manejarError(res)
  return res.json()
}

export class ResultadoExpirado extends Error {}

export async function descargarResultado(jobId: string): Promise<{ blob: Blob; nombre: string }> {
  const res = await fetch(`/api/descargar/${jobId}`)
  if (res.status === 404) throw new ResultadoExpirado('El resultado ya no está disponible en el servidor.')
  if (!res.ok) return manejarError(res)

  const disposicion = res.headers.get('Content-Disposition') ?? ''
  const coincidencia = /filename="?([^";]+)"?/.exec(disposicion)
  return { blob: await res.blob(), nombre: coincidencia?.[1] ?? 'resultado.zip' }
}

export async function eliminarResultado(jobId: string): Promise<void> {
  // Si falla no importa: el servidor lo borra solo al expirar
  await fetch(`/api/resultados/${jobId}`, { method: 'DELETE' }).catch(() => undefined)
}
