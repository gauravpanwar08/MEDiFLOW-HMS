import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { recordApi, patientApi } from '../services/api'
import useAuthStore from '../store/authStore'
import toast from 'react-hot-toast'

const TYPE_COLORS = { lab:'badge-blue', xray:'badge-purple', prescription:'badge-green', report:'badge-gray' }
const TYPE_ICONS  = { lab:'🧪', xray:'🩻', prescription:'💊', report:'📄' }

function UploadModal({ patientId, onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({ title:'', description:'', record_type:'report' })
  const [file, setFile] = useState(null)
  const ref = useRef()
  const mutation = useMutation(() => recordApi.upload(patientId, file, form), {
    onSuccess: () => { toast.success('Uploaded!'); qc.invalidateQueries(['records', patientId]); onClose() },
    onError: err => toast.error(err.response?.data?.detail || 'Upload failed'),
  })
  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header"><span className="modal-title">Upload Record</span><button className="modal-close" onClick={onClose}>✕</button></div>
        <form onSubmit={e => { e.preventDefault(); if (!file) { toast.error('Select a file'); return; } mutation.mutate() }}>
          <div className="modal-body">
            <div onClick={() => ref.current.click()} style={{ border:'2px dashed #d1d5db', borderRadius:8, padding:'28px 20px', textAlign:'center', cursor:'pointer', marginBottom:16, background: file ? '#f0fdf4':'#fafafa', borderColor: file ? '#16a34a':'#d1d5db' }}>
              <div style={{ fontSize:32 }}>{file ? '✅':'📁'}</div>
              <div style={{ fontSize:13, fontWeight:500, marginTop:8 }}>{file ? file.name : 'Click to select file'}</div>
              {file && <div style={{ fontSize:12, color:'#6b7280' }}>{(file.size/1024).toFixed(1)} KB</div>}
              <div style={{ fontSize:12, color:'#9ca3af', marginTop:4 }}>PDF, JPG, PNG (max 10MB)</div>
              <input ref={ref} type="file" style={{ display:'none' }} accept=".pdf,.jpg,.jpeg,.png" onChange={e => setFile(e.target.files[0])} />
            </div>
            <div className="form-group"><label className="form-label">Title</label><input className="form-control" value={form.title} onChange={e => setForm(p=>({...p,title:e.target.value}))} /></div>
            <div className="form-group"><label className="form-label">Type</label>
              <select className="form-control" value={form.record_type} onChange={e => setForm(p=>({...p,record_type:e.target.value}))}>
                <option value="report">Report</option><option value="lab">Lab Result</option>
                <option value="xray">X-Ray/Scan</option><option value="prescription">Prescription</option>
              </select>
            </div>
            <div className="form-group"><label className="form-label">Description</label><textarea className="form-control" rows={2} value={form.description} onChange={e => setForm(p=>({...p,description:e.target.value}))} /></div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={mutation.isLoading || !file}>{mutation.isLoading ? 'Uploading...':'Upload'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function MedicalRecords() {
  const { user } = useAuthStore()
  const [showUpload, setShowUpload] = useState(false)
  const [page, setPage] = useState(1)
  const isPatient = user?.role === 'patient'
  const canUpload = ['admin','super_admin','doctor'].includes(user?.role)

  const { data: myProfile } = useQuery('my-patient-profile', () => patientApi.myProfile().then(r => r.data), { enabled: isPatient, retry: false })
  const patientId = isPatient ? myProfile?.id : null

  const { data, isLoading } = useQuery(
    ['records', patientId, page],
    () => recordApi.list(patientId, { page, page_size: 20 }).then(r => r.data),
    { enabled: !isPatient || !!patientId, keepPreviousData: true }
  )

  const download = async (id, name) => {
    try { const blob = await recordApi.download(id); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href=url; a.download=name; a.click(); URL.revokeObjectURL(url) }
    catch { toast.error('Download failed') }
  }

  if (isPatient && !myProfile) return (
    <div className="card" style={{ padding:32, textAlign:'center' }}>
      <div style={{ fontSize:40, marginBottom:12 }}>👤</div>
      <p style={{ fontWeight:600 }}>Complete Your Patient Profile First</p>
      <p className="text-muted" style={{ marginTop:8 }}>Go to Profile → fill in your patient details → return here.</p>
    </div>
  )

  return (
    <div>
      <div className="toolbar">
        <span style={{ flex:1, fontSize:13, color:'#6b7280' }}>{data?.total || 0} records</span>
        {canUpload && patientId && <button className="btn btn-primary" onClick={() => setShowUpload(true)}>↑ Upload</button>}
      </div>
      <div className="card">
        {isLoading ? <div className="loading"><div className="spinner"/></div>
        : !data?.items?.length ? <div className="empty-state"><div style={{fontSize:48}}>📁</div><p>No records yet</p></div>
        : (
          <>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Title</th><th>Type</th><th>File</th><th>Date</th><th>Action</th></tr></thead>
                <tbody>
                  {data.items.map(r => (
                    <tr key={r.id}>
                      <td><div style={{fontWeight:500}}>{r.title||r.file_name}</div>{r.description&&<div style={{fontSize:12,color:'#6b7280'}}>{r.description}</div>}</td>
                      <td><span className={`badge ${TYPE_COLORS[r.record_type]||'badge-gray'}`}>{TYPE_ICONS[r.record_type]} {r.record_type}</span></td>
                      <td><div style={{fontSize:12}}>{r.file_name}</div><div style={{fontSize:11,color:'#9ca3af'}}>{(r.file_size/1024).toFixed(1)} KB</div></td>
                      <td style={{fontSize:12,color:'#6b7280'}}>{new Date(r.created_at).toLocaleDateString()}</td>
                      <td><button className="btn btn-secondary btn-sm" onClick={() => download(r.id, r.file_name)}>↓ Download</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="pagination">
              <span className="pagination-info">{data.total} records · Page {data.page} of {data.pages}</span>
              <div className="pagination-controls">
                <button className="page-btn" disabled={page<=1} onClick={() => setPage(p=>p-1)}>←</button>
                <button className="page-btn active">{page}</button>
                <button className="page-btn" disabled={page>=data.pages} onClick={() => setPage(p=>p+1)}>→</button>
              </div>
            </div>
          </>
        )}
      </div>
      {showUpload && patientId && <UploadModal patientId={patientId} onClose={() => setShowUpload(false)} />}
    </div>
  )
}
