import { useState } from 'react'
import { useQuery } from 'react-query'
import { auditApi } from '../services/api'

const ACTION_COLORS = { create:'badge-green', update:'badge-blue', delete:'badge-red', login:'badge-gray', logout:'badge-gray', access:'badge-gray' }

export default function AuditLogs() {
  const [filters, setFilters] = useState({ page:1, resource_type:'' })
  const [selected, setSelected] = useState(null)

  const { data, isLoading } = useQuery(
    ['audit', filters],
    () => auditApi.list({ ...filters, page_size:25 }).then(r => r.data),
    { keepPreviousData: true }
  )

  return (
    <div style={{ display:'grid', gridTemplateColumns: selected ? '1fr 340px' : '1fr', gap:20 }}>
      <div>
        <div className="toolbar">
          <select className="form-control" style={{width:'auto'}} value={filters.resource_type}
            onChange={e => setFilters(p=>({...p,resource_type:e.target.value,page:1}))}>
            <option value="">All Resources</option>
            {['user','appointment','patient','doctor','medical_record'].map(r=><option key={r} value={r}>{r}</option>)}
          </select>
          <span style={{fontSize:13,color:'#6b7280'}}>{data?.total||0} entries</span>
        </div>
        <div className="card">
          {isLoading ? <div className="loading"><div className="spinner"/></div>
          : !data?.items?.length ? <div className="empty-state"><p>No audit logs</p></div>
          : (
            <>
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Time</th><th>User</th><th>Action</th><th>Resource</th><th>IP</th></tr></thead>
                  <tbody>
                    {data.items.map(log=>(
                      <tr key={log.id} style={{cursor:'pointer', background: selected?.id===log.id ? '#eff6ff':''}}
                        onClick={()=>setSelected(selected?.id===log.id ? null : log)}>
                        <td style={{fontSize:12,whiteSpace:'nowrap'}}>{new Date(log.created_at).toLocaleString()}</td>
                        <td style={{fontSize:12}}>{log.user ? `${log.user.first_name} ${log.user.last_name}` : <span className="text-muted">System</span>}</td>
                        <td><span className={`badge ${ACTION_COLORS[log.action]||'badge-gray'}`}>{log.action}</span></td>
                        <td><span style={{fontWeight:500}}>{log.resource_type}</span>{log.resource_id&&<span className="text-muted"> #{log.resource_id}</span>}</td>
                        <td style={{fontSize:12,color:'#6b7280',fontFamily:'monospace'}}>{log.ip_address||'—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="pagination">
                <span className="pagination-info">{data.total} entries · Page {data.page} of {data.pages}</span>
                <div className="pagination-controls">
                  <button className="page-btn" disabled={filters.page<=1} onClick={()=>setFilters(p=>({...p,page:p.page-1}))}>←</button>
                  <button className="page-btn active">{filters.page}</button>
                  <button className="page-btn" disabled={filters.page>=data.pages} onClick={()=>setFilters(p=>({...p,page:p.page+1}))}>→</button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
      {selected && (
        <div className="card" style={{alignSelf:'start',position:'sticky',top:76}}>
          <div className="card-header"><span className="card-title">Log #{selected.id}</span><button className="modal-close" onClick={()=>setSelected(null)}>✕</button></div>
          <div className="card-body">
            {[['Time', new Date(selected.created_at).toLocaleString()],
              ['Action', <span className={`badge ${ACTION_COLORS[selected.action]}`}>{selected.action}</span>],
              ['Resource', `${selected.resource_type} #${selected.resource_id||'—'}`],
              ['User', selected.user ? `${selected.user.first_name} ${selected.user.last_name}` : 'System'],
              ['IP', <code style={{fontSize:12}}>{selected.ip_address||'—'}</code>],
              ...(selected.notes ? [['Notes', selected.notes]] : []),
            ].map(([label, value]) => (
              <div key={label} style={{marginBottom:12}}>
                <div style={{fontSize:11,fontWeight:600,color:'#9ca3af',textTransform:'uppercase',marginBottom:3}}>{label}</div>
                <div style={{fontSize:13,color:'#374151'}}>{value}</div>
              </div>
            ))}
            {selected.old_values && <><div style={{fontSize:11,fontWeight:600,color:'#9ca3af',marginBottom:4}}>BEFORE</div><pre style={{background:'#fee2e2',padding:10,borderRadius:6,fontSize:11,overflow:'auto',maxHeight:150}}>{JSON.stringify(selected.old_values,null,2)}</pre></>}
            {selected.new_values && <><div style={{fontSize:11,fontWeight:600,color:'#9ca3af',marginBottom:4,marginTop:8}}>AFTER</div><pre style={{background:'#dcfce7',padding:10,borderRadius:6,fontSize:11,overflow:'auto',maxHeight:150}}>{JSON.stringify(selected.new_values,null,2)}</pre></>}
          </div>
        </div>
      )}
    </div>
  )
}
