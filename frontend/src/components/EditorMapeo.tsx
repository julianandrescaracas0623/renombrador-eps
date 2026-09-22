import { IconTrash } from '../icons'

export interface ParPrefijo {
  origen: string
  destino: string
}

interface Props {
  pares: ParPrefijo[]
  onCambiar: (pares: ParPrefijo[]) => void
}

export default function EditorMapeo({ pares, onCambiar }: Props) {
  function actualizarPar(indice: number, campo: keyof ParPrefijo, valor: string) {
    const copia = pares.map((par, i) => (i === indice ? { ...par, [campo]: valor } : par))
    onCambiar(copia)
  }

  function agregarPar() {
    onCambiar([...pares, { origen: '', destino: '' }])
  }

  function quitarPar(indice: number) {
    onCambiar(pares.filter((_, i) => i !== indice))
  }

  return (
    <div className="campo">
      <span className="etiqueta-campo">Mapeo de prefijos</span>
      <p className="ayuda">Cada fila reemplaza el prefijo de "Origen" por "Destino" al inicio del PDF.</p>

      <div className="tabla-mapeo">
        {pares.map((par, indice) => (
          <div className="fila-mapeo" key={indice}>
            <input
              type="text"
              placeholder="Origen (ej. SI)"
              value={par.origen}
              onChange={(e) => actualizarPar(indice, 'origen', e.target.value)}
            />
            <span className="flecha">&rarr;</span>
            <input
              type="text"
              placeholder="Destino (ej. FEV_900472731_SI)"
              value={par.destino}
              onChange={(e) => actualizarPar(indice, 'destino', e.target.value)}
            />
            <button
              type="button"
              className="boton-icono boton-icono-peligro"
              onClick={() => quitarPar(indice)}
              aria-label="Quitar prefijo"
            >
              <IconTrash />
            </button>
          </div>
        ))}
      </div>

      <button type="button" className="boton-secundario" onClick={agregarPar}>
        + Agregar prefijo
      </button>
    </div>
  )
}
