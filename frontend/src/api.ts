export interface EpsConfig {
  id: string
  nombre: string
  modo_salida: 'unico' | 'soporte_rips'
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
}

export interface ProcesarResponse {
  job_id: string
  eps: string
  resumen: ResumenArchivo[]
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

export function urlDescarga(jobId: string): string {
  return `/api/descargar/${jobId}`
}
