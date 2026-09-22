import { useEffect, useState } from 'react'
import './App.css'
import { obtenerEps, procesarArchivos } from './api'
import type { EpsConfig, ProcesarResponse } from './api'
import SelectorEps from './components/SelectorEps'
import EditorMapeo from './components/EditorMapeo'
import type { ParPrefijo } from './components/EditorMapeo'
import SubidaArchivos from './components/SubidaArchivos'
import PanelResultado from './components/PanelResultado'
import { IconMoon, IconSpinner, IconSun, IconWarning } from './icons'

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
  const [resultado, setResultado] = useState<ProcesarResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

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
    setResultado(null)
  }

  async function procesar() {
    setError(null)
    setResultado(null)

    if (archivos.length === 0) {
      setError('Sube al menos un archivo ZIP.')
      return
    }

    setEstado('procesando')

    try {
      const respuesta = await procesarArchivos(epsSeleccionada, mapeoAObjeto(mapeo), archivos)
      setResultado(respuesta)
      setEstado('listo')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error inesperado.')
      setEstado('listo')
    }
  }

  function limpiarResultado() {
    setResultado(null)
    setArchivos([])
    setError(null)
  }

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
    <div className="contenedor">
      {botonTema}

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
      </main>

      {resultado && <PanelResultado resultado={resultado} onLimpiar={limpiarResultado} />}
    </div>
  )
}
