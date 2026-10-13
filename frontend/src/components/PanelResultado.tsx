import type { ResumenArchivo } from '../api'
import { IconWarning } from '../icons'
import { AVISOS } from '../avisos'

interface Props {
  resumen: ResumenArchivo[]
}

export default function PanelResultado({ resumen }: Props) {
  const totalPdfs = resumen.reduce((acc, r) => acc + r.pdfs_totales, 0)
  const totalRenombrados = resumen.reduce((acc, r) => acc + r.pdfs_renombrados, 0)
  const totalConflictos = resumen.reduce((acc, r) => acc + (r.conflictos_duplicados ?? 0), 0)

  return (
    <div className="detalle-resultado">
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-valor">{resumen.length}</span>
          <span className="stat-etiqueta">Archivo{resumen.length === 1 ? '' : 's'}</span>
        </div>
        <div className="stat-card">
          <span className="stat-valor">{totalPdfs}</span>
          <span className="stat-etiqueta">PDFs totales</span>
        </div>
        <div className="stat-card">
          <span className="stat-valor">{totalRenombrados}</span>
          <span className="stat-etiqueta">Renombrados</span>
        </div>
        <div className={`stat-card ${totalConflictos > 0 ? 'stat-card-alerta' : ''}`}>
          <span className="stat-valor">{totalConflictos}</span>
          <span className="stat-etiqueta">Duplicados</span>
        </div>
      </div>

      <div className="tabla-scroll">
      <table className="tabla-resumen">
        <thead>
          <tr>
            <th>Archivo</th>
            <th>PDFs</th>
            <th>Renombrados</th>
            <th>EPI omitidos</th>
            <th>Duplicados</th>
          </tr>
        </thead>
        <tbody>
          {resumen.map((item) => (
            <tr key={item.archivo}>
              <td>{item.archivo}</td>
              <td>{item.pdfs_totales}</td>
              <td>{item.pdfs_renombrados}</td>
              <td>{item.epi_omitidos ? 'Sí' : 'No'}</td>
              <td>{item.conflictos_duplicados ?? 0}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>

      {AVISOS.map(({ campo, titulo, ayuda }) => {
        const afectados = resumen.filter((item) => (item[campo] ?? []).length > 0)
        if (afectados.length === 0) return null

        return (
          <div className="aviso-cuv" key={campo}>
            <strong>
              <IconWarning size={16} /> {titulo}
            </strong>
            <p className="ayuda">{ayuda}</p>
            <ul>
              {afectados.map((item) => (
                <li key={item.archivo}>
                  <span className="aviso-cuv-archivo">{item.archivo}:</span>{' '}
                  {(item[campo] ?? []).join(', ')}
                </li>
              ))}
            </ul>
          </div>
        )
      })}
    </div>
  )
}
