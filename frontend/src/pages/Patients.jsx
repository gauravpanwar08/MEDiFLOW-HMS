import { useState } from 'react'
import { useQuery } from 'react-query'
import { patientApi } from '../services/api'

export default function Patients() {
  const [filters, setFilters] = useState({ search: '', page: 1 })
  const { data, isLoading } = useQuery(
    ['patients', filters],
    () => patientApi.list({ ...filters, page_size: 20 }).then(r => r.data),
    { keepPreviousData: true }
  )
  const age = dob => {
    if (!dob) return '—'
    return Math.floor((Date.now() - new Date(dob)) / (1000*60*60*24*365)) + 'y'
  }

  return (
    <div>
      <div className="toolbar">
        <div className="search-box" style={{ flex: 1 }}>
          <span>🔍</span>
          <input placeholder="Search patients..." value={filters.search}
            onChange={e => setFilters(p => ({ ...p, search: e.target.value, page: 1 }))} />
        </div>
      </div>
      <div className="card">
        {isLoading ? (
          <div className="loading"><div className="spinner" /></div>
        ) : !data?.items?.length ? (
          <div className="empty-state"><p>No patients found</p></div>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Patient</th><th>Age/Gender</th><th>Blood</th><th>Contact</th><th>Conditions</th></tr></thead>
                <tbody>
                  {data.items.map(p => (
                    <tr key={p.id}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <div className="avatar" style={{ width: 32, height: 32, fontSize: 12, flexShrink: 0 }}>
                            {p.user.first_name[0]}{p.user.last_name[0]}
                          </div>
                          <div>
                            <div style={{ fontWeight: 500 }}>{p.user.first_name} {p.user.last_name}</div>
                            <div style={{ fontSize: 12, color: '#6b7280' }}>{p.user.email}</div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <div>{age(p.date_of_birth)}</div>
                        <div style={{ fontSize: 12, color: '#6b7280', textTransform: 'capitalize' }}>{p.gender || '—'}</div>
                      </td>
                      <td>{p.blood_group ? <span className="badge badge-red">{p.blood_group}</span> : '—'}</td>
                      <td style={{ fontSize: 12 }}>{p.user.phone || '—'}</td>
                      <td style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12 }}>
                        {p.chronic_conditions || <span className="text-muted">None</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="pagination">
              <span className="pagination-info">{data.total} patients · Page {data.page} of {data.pages}</span>
              <div className="pagination-controls">
                <button className="page-btn" disabled={filters.page <= 1} onClick={() => setFilters(p => ({ ...p, page: p.page-1 }))}>←</button>
                <button className="page-btn active">{filters.page}</button>
                <button className="page-btn" disabled={filters.page >= data.pages} onClick={() => setFilters(p => ({ ...p, page: p.page+1 }))}>→</button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
