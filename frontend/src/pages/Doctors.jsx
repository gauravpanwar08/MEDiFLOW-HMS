import { useState } from 'react'
import { useQuery } from 'react-query'
import { doctorApi } from '../services/api'

export default function Doctors() {
  const [filters, setFilters] = useState({ search: '', specialty: '', page: 1 })
  const { data, isLoading } = useQuery(
    ['doctors', filters],
    () => doctorApi.list({ ...filters, page_size: 12 }).then(r => r.data),
    { keepPreviousData: true }
  )

  return (
    <div>
      <div className="toolbar">
        <div className="search-box" style={{ flex: 1 }}>
          <span>🔍</span>
          <input placeholder="Search doctors..." value={filters.search}
            onChange={e => setFilters(p => ({ ...p, search: e.target.value, page: 1 }))} />
        </div>
        <select className="form-control" style={{ width: 'auto' }} value={filters.specialty}
          onChange={e => setFilters(p => ({ ...p, specialty: e.target.value, page: 1 }))}>
          <option value="">All Specialties</option>
          {['Cardiologist','Dermatologist','Neurologist','Orthopedic Surgeon','Pediatrician',
            'Psychiatrist','General Physician','Gastroenterologist','Oncologist','Pulmonologist'].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div className="loading"><div className="spinner" /></div>
      ) : !data?.items?.length ? (
        <div className="empty-state"><p>No doctors found</p></div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(280px,1fr))', gap: 16 }}>
            {data.items.map(d => (
              <div key={d.id} className="card" style={{ padding: 20 }}>
                <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                  <div className="avatar" style={{ width: 48, height: 48, fontSize: 18, flexShrink: 0 }}>
                    {d.user.first_name[0]}{d.user.last_name[0]}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600 }}>Dr. {d.user.first_name} {d.user.last_name}</div>
                    <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>{d.specialty}</div>
                    <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                      <span className="badge badge-blue">{d.experience_years}y exp</span>
                      <span className={`badge ${d.is_available ? 'badge-green' : 'badge-red'}`}>
                        {d.is_available ? 'Available' : 'Unavailable'}
                      </span>
                      {d.consultation_fee > 0 && <span className="badge badge-gray">₹{d.consultation_fee}</span>}
                    </div>
                    <div style={{ fontSize: 12, color: '#6b7280', marginTop: 6 }}>
                      ⭐ {d.rating?.toFixed(1) || '—'} · {d.total_reviews} reviews
                    </div>
                    {d.qualification && <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>{d.qualification}</div>}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="pagination" style={{ marginTop: 16, background: 'transparent', border: 'none' }}>
            <span className="pagination-info">{data.total} doctors · Page {data.page} of {data.pages}</span>
            <div className="pagination-controls">
              <button className="page-btn" disabled={filters.page <= 1}
                onClick={() => setFilters(p => ({ ...p, page: p.page - 1 }))}>←</button>
              <button className="page-btn active">{filters.page}</button>
              <button className="page-btn" disabled={filters.page >= data.pages}
                onClick={() => setFilters(p => ({ ...p, page: p.page + 1 }))}>→</button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
