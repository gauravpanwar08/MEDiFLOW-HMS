import { useState } from 'react'
import { useMutation } from 'react-query'
import useAuthStore from '../store/authStore'
import { authApi } from '../services/api'
import toast from 'react-hot-toast'

const ROLE_STYLE = {
  admin:       { color:'#7c3aed', bg:'#f3e8ff', label:'Administrator' },
  super_admin: { color:'#dc2626', bg:'#fee2e2', label:'Super Admin' },
  doctor:      { color:'#2563eb', bg:'#eff6ff', label:'Doctor' },
  patient:     { color:'#16a34a', bg:'#dcfce7', label:'Patient' },
}

export default function Profile() {
  const { user, setUser } = useAuthStore()
  const [form, setForm] = useState({ first_name: user?.first_name||'', last_name: user?.last_name||'', phone: user?.phone||'' })
  const set = (k,v) => setForm(p=>({...p,[k]:v}))

  const mutation = useMutation(data => authApi.updateMe(data), {
    onSuccess: res => { toast.success('Profile updated!'); setUser(res.data) },
    onError: err => toast.error(err.response?.data?.detail||'Update failed'),
  })

  const rs = ROLE_STYLE[user?.role] || { color:'#6b7280', bg:'#f3f4f6', label: user?.role }
  const initials = user ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase() : '?'

  return (
    <div style={{ maxWidth:600, margin:'0 auto' }}>
      <div className="card" style={{ padding:28, marginBottom:20 }}>
        <div style={{ display:'flex', gap:20, alignItems:'center' }}>
          <div className="avatar" style={{ width:72, height:72, fontSize:28 }}>{initials}</div>
          <div>
            <h2 style={{fontSize:20,fontWeight:700}}>{user?.first_name} {user?.last_name}</h2>
            <div style={{fontSize:13,color:'#6b7280',marginTop:2}}>{user?.email}</div>
            <div style={{marginTop:8}}>
              <span style={{background:rs.bg,color:rs.color,padding:'3px 10px',borderRadius:20,fontSize:12,fontWeight:600}}>{rs.label}</span>
              {user?.is_verified && <span style={{marginLeft:8,background:'#dcfce7',color:'#15803d',padding:'3px 10px',borderRadius:20,fontSize:12}}>✓ Verified</span>}
            </div>
          </div>
        </div>
      </div>

      <div className="card" style={{marginBottom:20}}>
        <div className="card-header"><span className="card-title">Edit Profile</span></div>
        <div className="card-body">
          <form onSubmit={e=>{e.preventDefault();mutation.mutate(form)}}>
            <div className="form-row">
              <div className="form-group"><label className="form-label">First Name</label><input className="form-control" value={form.first_name} onChange={e=>set('first_name',e.target.value)} required /></div>
              <div className="form-group"><label className="form-label">Last Name</label><input className="form-control" value={form.last_name} onChange={e=>set('last_name',e.target.value)} required /></div>
            </div>
            <div className="form-group"><label className="form-label">Email</label><input className="form-control" value={user?.email} disabled style={{background:'#f9fafb',color:'#6b7280'}} /></div>
            <div className="form-group"><label className="form-label">Phone</label><input className="form-control" value={form.phone} onChange={e=>set('phone',e.target.value)} placeholder="+91 98765 43210" /></div>
            <button type="submit" className="btn btn-primary" disabled={mutation.isLoading}>{mutation.isLoading ? 'Saving...':'Save Changes'}</button>
          </form>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">Account Info</span></div>
        <div className="card-body">
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:16}}>
            {[['Role', rs.label], ['Hospital ID', user?.hospital_id], ['Status', user?.is_active ? '✅ Active':'❌ Inactive'],
              ['Member Since', user?.created_at ? new Date(user.created_at).toLocaleDateString():'—'],
              ['Last Login', user?.last_login ? new Date(user.last_login).toLocaleDateString():'—'],
              ['User ID', `#${user?.id}`]].map(([label,value])=>(
              <div key={label}>
                <div style={{fontSize:11,fontWeight:600,color:'#9ca3af',textTransform:'uppercase',marginBottom:4}}>{label}</div>
                <div style={{fontSize:13,fontWeight:500}}>{value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
