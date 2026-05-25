import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { appointmentApi, doctorApi } from '../services/api'
import useAuthStore from '../store/authStore'
import toast from 'react-hot-toast'

const STATUS_BADGE = { pending:'badge-yellow', confirmed:'badge-blue', completed:'badge-green', cancelled:'badge-red', no_show:'badge-gray' }
const PRIORITY_BADGE = { emergency:'badge-red', urgent:'badge-yellow', routine:'badge-gray' }

function BookModal({ onClose, doctors }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({ doctor_id:'', appointment_date:'', time_slot:'', reason:'', symptoms:'', priority:'routine' })
  const [slots, setSlots] = useState([])
  const [loadingSlots, setLoadingSlots] = useState(false)
  const set = (k, v) => setForm(p => ({ ...p, [k]: v }))

  const loadSlots = async (doctorId, date) => {
    if (!doctorId || !date) return
    setLoadingSlots(true)
    try {
      const r = await doctorApi.availableSlots(doctorId, date)
      setSlots(r.data)
    } catch { toast.error('Could not load slots') }
    finally { setLoadingSlots(false) }
  }

  const mutation = useMutation(data => appointmentApi.create(data), {
    onSuccess: () => { toast.success('Appointment booked!'); qc.invalidateQueries('appointments'); qc.invalidateQueries('today'); onClose() },
    onError: err => toast.error(err.response?.data?.detail || 'Booking failed'),
  })

  const submit = (e) => { e.preventDefault(); mutation.mutate({ ...form, doctor_id: +form.doctor_id }) }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <span className="modal-title">Book Appointment</span>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={submit}>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">Doctor *</label>
              <select className="form-control" value={form.doctor_id} required
                onChange={e => { set('doctor_id', e.target.value); set('time_slot', ''); loadSlots(e.target.value, form.appointment_date) }}>
                <option value="">Select doctor...</option>
                {(doctors || []).map(d => (
                  <option key={d.id} value={d.id}>Dr. {d.user.first_name} {d.user.last_name} — {d.specialty}</option>
                ))}
              </select>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Date *</label>
                <input type="date" className="form-control" min={new Date().toISOString().split('T')[0]}
                  value={form.appointment_date} required
                  onChange={e => { set('appointment_date', e.target.value); set('time_slot', ''); loadSlots(form.doctor_id, e.target.value) }} />
              </div>
              <div className="form-group">
                <label className="form-label">Priority</label>
                <select className="form-control" value={form.priority} onChange={e => set('priority', e.target.value)}>
                  <option value="routine">Routine</option>
                  <option value="urgent">Urgent</option>
                  <option value="emergency">Emergency</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Time Slot *</label>
              {loadingSlots && <p style={{ fontSize: 12, color: '#6b7280' }}>Loading slots...</p>}
              {!loadingSlots && slots.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 6 }}>
                  {slots.map(s => (
                    <button key={s.time} type="button" disabled={!s.available}
                      onClick={() => set('time_slot', s.time)}
                      style={{
                        padding: '6px 12px', borderRadius: 6, fontSize: 12, border: '1px solid',
                        borderColor: form.time_slot === s.time ? '#2563eb' : s.available ? '#d1d5db' : '#e5e7eb',
                        background: form.time_slot === s.time ? '#2563eb' : s.available ? '#fff' : '#f9fafb',
                        color: form.time_slot === s.time ? '#fff' : s.available ? '#374151' : '#9ca3af',
                        cursor: s.available ? 'pointer' : 'not-allowed',
                      }}>
                      {s.time}
                    </button>
                  ))}
                </div>
              )}
              {!loadingSlots && slots.length === 0 && form.doctor_id && form.appointment_date && (
                <p style={{ fontSize: 12, color: '#6b7280' }}>No slots available for this date</p>
              )}
              {!form.doctor_id || !form.appointment_date ? (
                <p style={{ fontSize: 12, color: '#9ca3af' }}>Select doctor and date first</p>
              ) : null}
              <input className="form-control" style={{ marginTop: 8 }} placeholder="Or type manually e.g. 10:30"
                value={form.time_slot} onChange={e => set('time_slot', e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Reason</label>
              <input className="form-control" value={form.reason} onChange={e => set('reason', e.target.value)} placeholder="Reason for visit" />
            </div>
            <div className="form-group">
              <label className="form-label">Symptoms</label>
              <textarea className="form-control" rows={3} value={form.symptoms} onChange={e => set('symptoms', e.target.value)} placeholder="Describe symptoms..." />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={mutation.isLoading || !form.time_slot}>
              {mutation.isLoading ? 'Booking...' : 'Book Appointment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function UpdateModal({ appt, onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    status: appt.status, notes: appt.notes || '',
    diagnosis: appt.diagnosis || '', prescription: appt.prescription || '',
    cancelled_reason: '',
  })
  const set = (k, v) => setForm(p => ({ ...p, [k]: v }))
  const mutation = useMutation(data => appointmentApi.update(appt.id, data), {
    onSuccess: () => { toast.success('Updated!'); qc.invalidateQueries('appointments'); onClose() },
    onError: err => toast.error(err.response?.data?.detail || 'Update failed'),
  })
  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <span className="modal-title">Update Appointment #{appt.id}</span>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={e => { e.preventDefault(); mutation.mutate(form) }}>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">Status</label>
              <select className="form-control" value={form.status} onChange={e => set('status', e.target.value)}>
                {['pending','confirmed','completed','cancelled','no_show'].map(s => (
                  <option key={s} value={s}>{s.replace('_',' ')}</option>
                ))}
              </select>
            </div>
            {form.status === 'cancelled' && (
              <div className="form-group">
                <label className="form-label">Cancellation Reason</label>
                <input className="form-control" value={form.cancelled_reason} onChange={e => set('cancelled_reason', e.target.value)} />
              </div>
            )}
            <div className="form-group">
              <label className="form-label">Notes</label>
              <textarea className="form-control" rows={2} value={form.notes} onChange={e => set('notes', e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Diagnosis</label>
              <textarea className="form-control" rows={2} value={form.diagnosis} onChange={e => set('diagnosis', e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Prescription</label>
              <textarea className="form-control" rows={2} value={form.prescription} onChange={e => set('prescription', e.target.value)} />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={mutation.isLoading}>Save Changes</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Appointments() {
  const { user } = useAuthStore()
  const [showBook, setShowBook] = useState(false)
  const [editAppt, setEditAppt] = useState(null)
  const [filters, setFilters] = useState({ status: '', priority: '', page: 1 })

  const { data, isLoading } = useQuery(
    ['appointments', filters],
    () => appointmentApi.list({ ...filters, page_size: 15 }).then(r => r.data),
    { keepPreviousData: true }
  )

  const { data: doctors } = useQuery('doctors-all',
    () => doctorApi.list({ page_size: 100, available_only: true }).then(r => r.data.items),
    { enabled: user?.role !== 'doctor' }
  )

  const canEdit = ['admin', 'super_admin', 'doctor'].includes(user?.role)

  return (
    <div>
      <div className="toolbar">
        <select className="form-control" style={{ width: 'auto' }} value={filters.status}
          onChange={e => setFilters(p => ({ ...p, status: e.target.value, page: 1 }))}>
          <option value="">All Status</option>
          {['pending','confirmed','completed','cancelled','no_show'].map(s => (
            <option key={s} value={s}>{s.replace('_',' ')}</option>
          ))}
        </select>
        <select className="form-control" style={{ width: 'auto' }} value={filters.priority}
          onChange={e => setFilters(p => ({ ...p, priority: e.target.value, page: 1 }))}>
          <option value="">All Priority</option>
          <option value="emergency">Emergency</option>
          <option value="urgent">Urgent</option>
          <option value="routine">Routine</option>
        </select>
        <div style={{ flex: 1 }} />
        <button className="btn btn-primary" onClick={() => setShowBook(true)}>+ Book Appointment</button>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="loading"><div className="spinner" /></div>
        ) : !data?.items?.length ? (
          <div className="empty-state"><p>No appointments found</p></div>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>#</th><th>Date & Time</th>
                    <th>{user?.role === 'patient' ? 'Doctor' : 'Patient'}</th>
                    <th>Reason</th><th>Priority</th><th>Status</th>
                    {canEdit && <th>Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {data.items.map(a => (
                    <tr key={a.id}>
                      <td style={{ color: '#9ca3af', fontSize: 12 }}>#{a.id}</td>
                      <td>
                        <div style={{ fontWeight: 600 }}>{a.appointment_date}</div>
                        <div style={{ fontSize: 12, color: '#6b7280' }}>{a.time_slot}</div>
                      </td>
                      <td>
                        {user?.role === 'patient'
                          ? <span>Dr. {a.doctor?.user?.first_name} {a.doctor?.user?.last_name}</span>
                          : <span>{a.patient?.user?.first_name} {a.patient?.user?.last_name}</span>}
                      </td>
                      <td style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {a.reason || <span className="text-muted">—</span>}
                      </td>
                      <td><span className={`badge ${PRIORITY_BADGE[a.priority]}`}>{a.priority}</span></td>
                      <td><span className={`badge ${STATUS_BADGE[a.status]}`}>{a.status}</span></td>
                      {canEdit && (
                        <td><button className="btn btn-secondary btn-sm" onClick={() => setEditAppt(a)}>Edit</button></td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="pagination">
              <span className="pagination-info">{data.total} total · Page {data.page} of {data.pages}</span>
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

      {showBook && <BookModal onClose={() => setShowBook(false)} doctors={doctors} />}
      {editAppt && <UpdateModal appt={editAppt} onClose={() => setEditAppt(null)} />}
    </div>
  )
}
