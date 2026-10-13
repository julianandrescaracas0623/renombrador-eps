import { useCallback, useEffect, useState } from 'react'
import './App.css'
import { descargarResultado, eliminarResultado, obtenerEps, procesarArchivos, ResultadoExpirado } from './api'
import type { EpsConfig } from './api'
import SelectorEps from './components/SelectorEps'
import EditorMapeo from './components/EditorMapeo'
import type { ParPrefijo } from './components/EditorMapeo'
import SubidaArchivos from './components/SubidaArchivos'
import Historial from './components/Historial'
import ModalConfirmacion from './components/ModalConfirmacion'
import type { EntradaHistorial } from './components/Historial'
import { IconHistorial, IconMoon, IconSpinner, IconSun, IconTrash, IconWarning } from './icons'

type Estado = 'cargando' | 'listo' | 'procesando' | 'error-inicial'
type Tema = 'light' | 'dark'

function obtenerTemaInicial(): Tema {
  try {
    const guardado = localStorage.getItem('tema')
    if (guardado === 'light' || guardado === 'dark') return guardado
  } catch {
    // localStorage no disponible (ej. navegación privada): se ignora
  }

  if (window.matchMedia?.('(prefers-color-scheme: dark)').matches) return 'dark'
  return 'light'
}

const CLAVE_HISTORIAL = 'historial'

function cargarHistorial(): EntradaHistorial[] {
  try {
    const guardado = localStorage.getItem(CLAVE_HISTORIAL)
    const lista: unknown = guardado ? JSON.parse(guardado) : []
    return Array.isArray(lista) ? (lista as EntradaHistorial[]) : []
  } catch {
    return []
  }
}

function mapeoAObjeto(pares: ParPrefijo[]): string {
  return pares
    .filter((p) => p.origen.trim() && p.destino.trim())
    .map((p) => `${p.origen.trim()}=${p.destino.trim()}`)
    .join('\n')
}

function objetoAMapeo(mapeo: Record<string, string>): ParPrefijo[] {
  const pares = Object.entries(mapeo).map(([origen, destino]) => ({ origen, destino }))
  return pares.length > 0 ? pares : [{ origen: '', destino: '' }]
}

export default function App() {
  const [tema, setTema] = useState<Tema>(obtenerTemaInicial)
  const [estado, setEstado] = useState<Estado>('cargando')
  const [epsList, setEpsList] = useState<EpsConfig[]>([])
  const [epsSeleccionada, setEpsSeleccionada] = useState('')
  const [mapeo, setMapeo] = useState<ParPrefijo[]>([])
  const [archivos, setArchivos] = useState<File[]>([])
  const [historial, setHistorial] = useState<EntradaHistorial[]>(cargarHistorial)
  const [seleccionados, setSeleccionados] = useState<Set<string>>(new Set())
  const [abierta, setAbierta] = useState<string | null>(null)
  const [historialVisible, setHistorialVisible] = useState(false)
  const [confirmandoEliminar, setConfirmandoEliminar] = useState(false)
  const [descargando, setDescargando] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    try {
      localStorage.setItem(CLAVE_HISTORIAL, JSON.stringify(historial))
    } catch {
      // localStorage no disponible o lleno: el historial solo dura la sesión
    }
  }, [historial])

  useEffect(() => {
    document.documentElement.dataset.theme = tema

    try {
      localStorage.setItem('tema', tema)
    } catch {
      // localStorage no disponible: la preferencia solo dura la sesión
    }
  }, [tema])

  function alternarTema() {
    setTema((actual) => (actual === 'light' ? 'dark' : 'light'))
  }

  useEffect(() => {
    obtenerEps()
      .then((lista) => {
        setEpsList(lista)
        if (lista.length > 0) {
          setEpsSeleccionada(lista[0].id)
          setMapeo(objetoAMapeo(lista[0].mapeo_default))
        }
        setEstado('listo')
      })
      .catch((err: Error) => {
        setError(err.message)
        setEstado('error-inicial')
      })
  }, [])

  function seleccionarEps(id: string) {
    setEpsSeleccionada(id)
    const eps = epsList.find((e) => e.id === id)
    if (eps) setMapeo(objetoAMapeo(eps.mapeo_default))
  }

  async function procesar() {
    setError(null)

    if (archivos.length === 0) {
      setError('Sube al menos un archivo ZIP.')
      return
    }

    setEstado('procesando')

    try {
      const respuesta = await procesarArchivos(epsSeleccionada, mapeoAObjeto(mapeo), archivos)
      const ahora = Date.now()
      const entrada: EntradaHistorial = {
        id: respuesta.job_id,
        fecha: new Date(ahora).toISOString(),
        expira: new Date(ahora + respuesta.expira_en * 1000).toISOString(),
        eps: respuesta.eps,
        resumen: respuesta.resumen,
      }
      setHistorial((actual) => [entrada, ...actual])
      setAbierta(entrada.id)
      setHistorialVisible(true)
      setArchivos([])
      setEstado('listo')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error inesperado.')
      setEstado('listo')
    }
  }

  async function descargar(entrada: EntradaHistorial) {
    setError(null)
    setDescargando(entrada.id)

    try {
      const { blob, nombre } = await descargarResultado(entrada.id)
      const url = URL.createObjectURL(blob)
      const enlace = document.createElement('a')
      enlace.href = url
      enlace.download = nombre
      enlace.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (err) {
      if (err instanceof ResultadoExpirado) {
        setHistorial((actual) => actual.map((e) => (e.id === entrada.id ? { ...e, expirado: true } : e)))
      }
      setError(err instanceof Error ? err.message : 'No se pudo descargar.')
    } finally {
      setDescargando(null)
    }
  }

  function pedirEliminarSeleccionados() {
    if (seleccionados.size > 0) setConfirmandoEliminar(true)
  }

  function eliminarSeleccionados() {
    setConfirmandoEliminar(false)
    seleccionados.forEach((id) => void eliminarResultado(id))
    setHistorial((actual) => actual.filter((e) => !seleccionados.has(e.id)))
    setSeleccionados(new Set())
  }

  const cantidadEliminar = seleccionados.size
  const eliminaTodo = cantidadEliminar > 1 && cantidadEliminar === historial.length

  const cerrarHistorial = useCallback(() => setHistorialVisible(false), [])

  const botonTema = (
    <button
      type="button"
      className="boton-tema"
      onClick={alternarTema}
      aria-label={tema === 'light' ? 'Cambiar a modo oscuro' : 'Cambiar a modo claro'}
      title={tema === 'light' ? 'Modo oscuro' : 'Modo claro'}
    >
      {tema === 'light' ? <IconMoon /> : <IconSun />}
    </button>
  )

  if (estado === 'cargando') {
    return (
      <div className="contenedor contenedor-centrado">
        {botonTema}
        <IconSpinner size={28} />
        <p>Cargando…</p>
      </div>
    )
  }

  if (estado === 'error-inicial') {
    return (
      <div className="contenedor contenedor-centrado">
        {botonTema}
        <IconWarning size={28} />
        <p>No se pudo conectar con el servidor. {error}</p>
      </div>
    )
  }

  return (
    <div className={`contenedor ${historialVisible ? 'con-historial' : ''}`}>
      {botonTema}

      <button
        type="button"
        className="boton-historial"
        onClick={() => setHistorialVisible((v) => !v)}
        aria-expanded={historialVisible}
      >
        <IconHistorial size={17} />
        Historial
        {historial.length > 0 && <span className="boton-historial-contador">{historial.length}</span>}
      </button>

      <header className="encabezado">
        <h1>Renombrador de soportes EPS</h1>
        <p className="subtitulo">
          Sube tus ZIP, elige la EPS y descarga los archivos ya renombrados y listos para radicar.
        </p>
      </header>

      <main className="tarjeta">
        <div className="paso">
          <span className="paso-numero">1</span>
          <SelectorEps epsList={epsList} epsSeleccionada={epsSeleccionada} onCambiar={seleccionarEps} />
        </div>

        <div className="paso">
          <span className="paso-numero">2</span>
          <EditorMapeo pares={mapeo} onCambiar={setMapeo} />
        </div>

        <div className="paso">
          <span className="paso-numero">3</span>
          <SubidaArchivos archivos={archivos} onCambiar={setArchivos} />
        </div>

        {error && (
          <p className="error">
            <IconWarning size={16} /> {error}
          </p>
        )}

        <div className="acciones-principales">
          <button
            type="button"
            className="boton-principal"
            onClick={procesar}
            disabled={estado === 'procesando'}
          >
            {estado === 'procesando' ? (
              <>
                <IconSpinner size={18} /> Procesando…
              </>
            ) : (
              'Procesar y generar descarga'
            )}
          </button>
          <button
            type="button"
            className="boton-eliminar"
            onClick={pedirEliminarSeleccionados}
            disabled={seleccionados.size === 0}
            title="Selecciona procesos en el historial para eliminarlos"
          >
            <IconTrash size={17} />
            Eliminar{seleccionados.size > 0 ? ` (${seleccionados.size})` : ''}
          </button>
        </div>
      </main>

      <Historial
        visible={historialVisible}
        onCerrar={cerrarHistorial}
        onEliminar={pedirEliminarSeleccionados}
        entradas={historial}
        seleccionados={seleccionados}
        abierta={abierta}
        descargando={descargando}
        onSeleccionar={setSeleccionados}
        onAbrir={setAbierta}
        onDescargar={descargar}
      />

      <ModalConfirmacion
        abierto={confirmandoEliminar}
        titulo={eliminaTodo ? '¿Eliminar todo el historial?' : '¿Eliminar del historial?'}
        mensaje={`Se ${cantidadEliminar === 1 ? 'borrará 1 proceso' : `borrarán ${cantidadEliminar} procesos`} y sus descargas dejarán de estar disponibles. Esta acción no se puede deshacer.`}
        textoConfirmar={eliminaTodo ? 'Eliminar todo' : `Eliminar ${cantidadEliminar}`}
        onConfirmar={eliminarSeleccionados}
        onCancelar={() => setConfirmandoEliminar(false)}
      />
    </div>
  )
}
