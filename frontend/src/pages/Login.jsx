import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '', hospitalSlug: 'default' })
  const { login, isLoading, error } = useAuthStore()
  const navigate = useNavigate()
  const set = (k, v) => setForm(p => ({ ...p, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const res = await login(form.email, form.password, form.hospitalSlug)
    if (res.success) navigate('/dashboard')
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <div style={{ fontSize: 40 }}>🏥</div>
          <h2>MediCore HMS</h2>
          <p>Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Hospital Slug</label>
            <input className="form-control" value={form.hospitalSlug}
              onChange={e => set('hospitalSlug', e.target.value)} placeholder="default" required />
          </div>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input className="form-control" type="email" value={form.email}
              onChange={e => set('email', e.target.value)} placeholder="admin@hospital.com" required />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input className="form-control" type="password" value={form.password}
              onChange={e => set('password', e.target.value)} placeholder="••••••••" required />
          </div>

          {error && (
            <div style={{ background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 6,
              padding: '10px 12px', marginBottom: 16, fontSize: 13, color: '#b91c1c' }}>
              {error}
            </div>
          )}

          <button className="btn btn-primary w-full" type="submit" disabled={isLoading}
            style={{ justifyContent: 'center', padding: '10px' }}>
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: '#6b7280' }}>
          No account? <Link to="/register" style={{ color: '#2563eb', fontWeight: 500 }}>Register</Link>
        </p>

        <div style={{ marginTop: 20, padding: 12, background: '#f8fafc', borderRadius: 6, fontSize: 12, color: '#475569' }}>
          <strong>Demo accounts:</strong><br />
          Admin: admin@hospital.com / admin123<br />
          Doctor: doctor1@hospital.com / doctor123<br />
          Patient: patient1@email.com / patient123
        </div>
      </div>
    </div>
  )
}
