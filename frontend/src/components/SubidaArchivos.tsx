import { useRef, useState } from 'react'
import { IconFile, IconTrash, IconUpload } from '../icons'

interface Props {
  archivos: File[]
  onCambiar: (archivos: File[]) => void
}

function formatearTamano(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function SubidaArchivos({ archivos, onCambiar }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [arrastrando, setArrastrando] = useState(false)

  function agregarArchivos(lista: FileList | null) {
    if (!lista) return

    const nuevosZips = Array.from(lista).filter((f) => f.name.toLowerCase().endsWith('.zip'))
    onCambiar([...archivos, ...nuevosZips])
  }

  function quitarArchivo(indice: number) {
    onCambiar(archivos.filter((_, i) => i !== indice))
  }

  const tamanoTotal = archivos.reduce((acc, a) => acc + a.size, 0)

  return (
    <div className="campo">
      <span className="etiqueta-campo">Archivos ZIP</span>

      <div
        className={`zona-drop ${arrastrando ? 'arrastrando' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setArrastrando(true)
        }}
        onDragLeave={() => setArrastrando(false)}
        onDrop={(e) => {
          e.preventDefault()
          setArrastrando(false)
          agregarArchivos(e.dataTransfer.files)
        }}
      >
        <IconUpload />
        <p>
          <strong>Arrastra tus ZIP aquí</strong> o haz clic para seleccionarlos
        </p>
        <span className="zona-drop-ayuda">Solo archivos .zip · hasta 200 MB en total</span>
        <input
          ref={inputRef}
          type="file"
          accept=".zip"
          multiple
          hidden
          onChange={(e) => agregarArchivos(e.target.files)}
        />
      </div>

      {archivos.length > 0 && (
        <>
          <ul className="lista-archivos">
            {archivos.map((archivo, indice) => (
              <li key={`${archivo.name}-${indice}`}>
                <span className="lista-archivos-nombre">
                  <IconFile size={16} />
                  {archivo.name}
                </span>
                <span className="lista-archivos-tamano">{formatearTamano(archivo.size)}</span>
                <button
                  type="button"
                  className="boton-icono boton-icono-peligro"
                  onClick={() => quitarArchivo(indice)}
                  aria-label="Quitar archivo"
                >
                  <IconTrash size={15} />
                </button>
              </li>
            ))}
          </ul>
          <p className="ayuda ayuda-total">
            {archivos.length} archivo{archivos.length === 1 ? '' : 's'} · {formatearTamano(tamanoTotal)} en total
          </p>
        </>
      )}
    </div>
  )
}
