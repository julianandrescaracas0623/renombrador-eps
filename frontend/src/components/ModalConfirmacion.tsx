import { useEffect, useRef } from 'react'
import { IconTrash } from '../icons'

interface Props {
  abierto: boolean
  titulo: string
  mensaje: string
  textoConfirmar: string
  onConfirmar: () => void
  onCancelar: () => void
}

export default function ModalConfirmacion({
  abierto,
  titulo,
  mensaje,
  textoConfirmar,
  onConfirmar,
  onCancelar,
}: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  // <dialog> nativo: atrapa el foco, bloquea el fondo y cierra con Esc
  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return

    if (abierto && !dialog.open) dialog.showModal()
    if (!abierto && dialog.open) dialog.close()
  }, [abierto])

  return (
    <dialog
      ref={dialogRef}
      className="modal"
      aria-labelledby="modal-titulo"
      onCancel={(e) => {
        e.preventDefault()
        onCancelar()
      }}
      onClick={(e) => {
        // Clic en el fondo (fuera de la caja) cancela
        if (e.target === e.currentTarget) onCancelar()
      }}
    >
      <div className="modal-caja">
        <span className="modal-icono">
          <IconTrash size={22} />
        </span>
        <h2 id="modal-titulo">{titulo}</h2>
        <p>{mensaje}</p>

        <div className="modal-acciones">
          <button type="button" className="boton-secundario" onClick={onCancelar} autoFocus>
            Cancelar
          </button>
          <button type="button" className="boton-peligro" onClick={onConfirmar}>
            {textoConfirmar}
          </button>
        </div>
      </div>
    </dialog>
  )
}
