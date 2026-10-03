import type { EpsConfig } from '../api'
import { IconLayers } from '../icons'

interface Props {
  epsList: EpsConfig[]
  epsSeleccionada: string
  onCambiar: (id: string) => void
}

const DESCRIPCION_MODO: Record<string, string> = {
  unico: 'Entrega un solo ZIP renombrado.',
  soporte_rips: 'Separa en Sop.zip y Rips.zip, con una carpeta por factura.',
}

export default function SelectorEps({ epsList, epsSeleccionada, onCambiar }: Props) {
  return (
    <div className="campo">
      <span className="etiqueta-campo">EPS</span>
      <div className="grid-eps">
        {epsList.map((eps) => {
          const activa = eps.id === epsSeleccionada
          return (
            <button
              key={eps.id}
              type="button"
              className={`tarjeta-eps ${activa ? 'activa' : ''}`}
              onClick={() => onCambiar(eps.id)}
              aria-pressed={activa}
            >
              <IconLayers size={20} />
              <span className="tarjeta-eps-nombre">{eps.nombre}</span>
              <span className="tarjeta-eps-modo">
                {DESCRIPCION_MODO[eps.modo_salida] ?? eps.modo_salida}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
