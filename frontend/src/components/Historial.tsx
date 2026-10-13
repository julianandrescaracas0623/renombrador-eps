import { AVISOS } from '../avisos'
import type { ResumenArchivo } from '../api'
import { useEffect } from 'react'
import { IconCerrar, IconChevron, IconDownload, IconSpinner, IconTrash, IconWarning } from '../icons'
import PanelResultado from './PanelResultado'

export interface EntradaHistorial {
  id: string
  fecha: string
  expira: string
  eps: string
  resumen: ResumenArchivo[]
  expirado?: boolean
}

interface Props {
  visible: boolean
  onCerrar: () => void
  entradas: EntradaHistorial[]
  seleccionados: Set<string>
  abierta: string | null
  descargando: string | null
  onSeleccionar: (seleccionados: Set<string>) => void
  onAbrir: (id: string | null) => void
  onDescargar: (entrada: EntradaHistorial) => void
  onEliminar: () => void
}

const formatoFecha = new Intl.DateTimeFormat('es-CO', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

export function estaDisponible(entrada: EntradaHistorial): boolean {
  return !entrada.expirado && new Date(entrada.expira).getTime() > Date.now()
}

export default function Historial({
  visible,
  onCerrar,
  entradas,
  seleccionados,
  abierta,
  descargando,
  onSeleccionar,
  onAbrir,
  onDescargar,
  onEliminar,
}: Props) {
  useEffect(() => {
    if (!visible) return

    function alPresionarTecla(e: KeyboardEvent) {
      if (e.key === 'Escape') onCerrar()
    }

    window.addEventListener('keydown', alPresionarTecla)
    return () => window.removeEventListener('keydown', alPresionarTecla)
  }, [visible, onCerrar])

  const todosSeleccionados = entradas.length > 0 && entradas.every((e) => seleccionados.has(e.id))
  const algunoSeleccionado = entradas.some((e) => seleccionados.has(e.id))

  function alternarTodos() {
    onSeleccionar(todosSeleccionados ? new Set() : new Set(entradas.map((e) => e.id)))
  }

  function alternar(id: string) {
    const nuevos = new Set(seleccionados)
    if (nuevos.has(id)) nuevos.delete(id)
    else nuevos.add(id)
    onSeleccionar(nuevos)
  }

  return (
    <>
      <div
        className={`historial-fondo ${visible ? 'visible' : ''}`}
        onClick={onCerrar}
        aria-hidden="true"
      />
      <aside
        className={`historial-lateral ${visible ? 'visible' : ''}`}
        aria-label="Historial"
        aria-hidden={!visible}
        inert={!visible}
      >
        <div className="historial-encabezado">
          <h2>Historial</h2>
          <button type="button" className="boton-icono" onClick={onCerrar} aria-label="Cerrar historial">
            <IconCerrar size={16} />
          </button>
        </div>

        {entradas.length > 0 && (
          <div className="historial-barra">
            <label className="historial-check">
              <input
                type="checkbox"
                checked={todosSeleccionados}
                ref={(el) => {
                  if (el) el.indeterminate = algunoSeleccionado && !todosSeleccionados
                }}
                onChange={alternarTodos}
              />
              Seleccionar todo
            </label>
            {seleccionados.size > 0 && (
              <button type="button" className="boton-texto boton-texto-peligro" onClick={onEliminar}>
                <IconTrash size={15} />
                Eliminar ({seleccionados.size})
              </button>
            )}
          </div>
        )}

        {entradas.length === 0 ? (
          <p className="ayuda historial-vacio">
            Aún no has procesado archivos. Cada proceso aparecerá aquí con su fecha y hora.
          </p>
        ) : (
          <ul className="historial-lista">
            {entradas.map((entrada) => {
              const disponible = estaDisponible(entrada)
              const totalRenombrados = entrada.resumen.reduce((acc, r) => acc + r.pdfs_renombrados, 0)
              const conAvisos = entrada.resumen.some((r) => AVISOS.some(({ campo }) => (r[campo] ?? []).length > 0))
              const estaAbierta = abierta === entrada.id

              return (
                <li
                  key={entrada.id}
                  className={`historial-item ${seleccionados.has(entrada.id) ? 'seleccionado' : ''}`}
                >
                  <div className="historial-fila">
                    <input
                      type="checkbox"
                      checked={seleccionados.has(entrada.id)}
                      onChange={() => alternar(entrada.id)}
                      aria-label={`Seleccionar proceso del ${formatoFecha.format(new Date(entrada.fecha))}`}
                    />

                    <button
                      type="button"
                      className="historial-info"
                      onClick={() => onAbrir(estaAbierta ? null : entrada.id)}
                      aria-expanded={estaAbierta}
                    >
                      <span className="historial-titulo">
                        <span className="historial-fecha">
                          <span className={`historial-chevron ${estaAbierta ? 'abierto' : ''}`}>
                            <IconChevron size={14} />
                          </span>
                          {formatoFecha.format(new Date(entrada.fecha))}
                        </span>
                        <span className="historial-eps">{entrada.eps}</span>
                        {conAvisos && (
                          <span className="historial-aviso" title="Hay facturas con documentos faltantes">
                            <IconWarning size={14} />
                          </span>
                        )}
                      </span>
                      <span className="historial-meta">
                        {entrada.resumen.length} archivo{entrada.resumen.length === 1 ? '' : 's'} ·{' '}
                        {totalRenombrados} renombrado{totalRenombrados === 1 ? '' : 's'}
                      </span>
                    </button>

                    {disponible ? (
                      <button
                        type="button"
                        className="boton-descarga boton-descarga-chico"
                        onClick={() => onDescargar(entrada)}
                        disabled={descargando === entrada.id}
                      >
                        {descargando === entrada.id ? <IconSpinner size={16} /> : <IconDownload size={16} />}
                        Descargar
                      </button>
                    ) : (
                      <span className="historial-expirado">Descarga expirada</span>
                    )}
                  </div>

                  {estaAbierta && <PanelResultado resumen={entrada.resumen} />}
                </li>
              )
            })}
          </ul>
        )}
      </aside>
    </>
  )
}
