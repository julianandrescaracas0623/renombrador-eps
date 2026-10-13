import type { ResumenArchivo } from '../api'
import { IconWarning } from '../icons'

interface Props {
  resumen: ResumenArchivo[]
}

export default function PanelResultado({ resumen }: Props) {
  const archivosConFacturasSinCuv = resumen.filter(
    (item) => (item.facturas_sin_cuv ?? []).length > 0,
  )

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

      {archivosConFacturasSinCuv.length > 0 && (
        <div className="aviso-cuv">
          <strong>
            <IconWarning size={16} /> Facturas sin CUV en el RIPS
          </strong>
          <p className="ayuda">
            Estas facturas no traían el archivo CUV dentro del ZIP subido. Revísalas antes de
            radicar en Horus.
          </p>
          <ul>
            {archivosConFacturasSinCuv.map((item) => (
              <li key={item.archivo}>
                <span className="aviso-cuv-archivo">{item.archivo}:</span>{' '}
                {(item.facturas_sin_cuv ?? []).join(', ')}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
