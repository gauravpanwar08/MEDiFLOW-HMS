import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Activity, User, Mail, Lock, Phone, Eye, EyeOff, Building2, ChevronDown, ArrowRight, Check } from 'lucide-react'
import { authApi } from '../services/api'
import toast from 'react-hot-toast'

const PATIENT_FEATURES = [
  { icon:'📅', label:'Smart Appointments', desc:'Schedule visits with verified hospital specialists' },
  { icon:'📁', label:'Medical Records',     desc:'View test results, diagnoses, and prescriptions' },
  { icon:'⏱️', label:'Queue Visibility',   desc:'Track consultation queue and estimated wait time' },
]

export default function Register() {
  const [form, setForm] = useState({
    first_name:'', last_name:'', email:'', password:'',
    phone:'', role:'patient', hospital_slug:'default',
  })
  const [showPw, setShowPw]   = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const set = (k, v) => setForm(p => ({ ...p, [k]: v }))

  /* password strength */
  const pwStr = (() => {
    const p = form.password; if (!p) return 0
    let s = 0
    if (p.length >= 8)        s++
    if (/[A-Z]/.test(p))     s++
    if (/[0-9]/.test(p))     s++
    if (/[^A-Za-z0-9]/.test(p)) s++
    return s
  })()
  const strLabel = ['','Weak','Fair','Good','Strong']
  const strColor = ['','#ef4444','#f97316','#eab308','#22c55e']

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.password.length < 8) { toast.error('Password must be at least 8 characters'); return }
    setLoading(true)
    try {
      await authApi.register({ ...form, role: 'patient' })
      toast.success('Patient account created! Please sign in.')
      navigate('/login')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={S.page}>
      <style>{css}</style>

      {/* ── LEFT PANEL ── */}
      <div style={S.left} className="auth-left">
        <div style={S.gridBg}/><div style={S.glow1}/><div style={S.glow2}/>

        <div style={{position:'relative',zIndex:1,width:'100%'}}>
          <div style={S.logoRow}>
            <div style={S.logoIcon}><Activity size={20} color="#fff"/></div>
            <span style={S.logoText}>MEDi<span style={{color:'#00C6A7'}}>FLOW</span></span>
          </div>

          <h1 style={S.leftH1}>
            Join the future<br/>
            <span style={S.grad}>of healthcare.</span>
          </h1>
          <p style={S.leftSub}>
            Create your patient portal account to manage appointments,
            access digital medical records, and connect with physicians.
          </p>

          {/* Feature list on left */}
          <div style={{display:'flex',flexDirection:'column',gap:10}}>
            {PATIENT_FEATURES.map(f => (
              <div key={f.label} style={{
                display:'flex', alignItems:'center', gap:12, padding:'11px 14px',
                borderRadius:12,
                background: 'rgba(255,255,255,.05)',
                border: '1px solid rgba(255,255,255,.08)',
              }}>
                <span style={{fontSize:20}}>{f.icon}</span>
                <div style={{flex:1}}>
                  <div style={{fontSize:13,fontWeight:600,color:'#f1f5f9'}}>{f.label}</div>
                  <div style={{fontSize:11.5,color:'#64748b',marginTop:1}}>{f.desc}</div>
                </div>
                <Check size={14} color="#00C6A7"/>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── RIGHT PANEL ── */}
      <div style={S.right}>
        <div style={S.card}>

          {/* mobile logo */}
          <div style={S.mobileLogo} className="auth-mobile-logo">
            <div style={S.logoIcon}><Activity size={17} color="#fff"/></div>
            <span style={{fontWeight:800,fontSize:'1rem',color:'#0A1628'}}>
              MEDi<span style={{color:'#00C6A7'}}>FLOW</span>
            </span>
          </div>

          <h2 style={S.cardTitle}>Create account</h2>
          <p  style={S.cardSub}>Join MEDiFLOW Hospital Management System</p>

          <form onSubmit={handleSubmit} noValidate>

            {/* Name row */}
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14,marginBottom:16}}>
              <div>
                <label style={S.label}>First name</label>
                <Inp icon={<User size={14} color="#94a3b8"/>} value={form.first_name}
                  onChange={e=>set('first_name',e.target.value)} placeholder="Rahul" required/>
              </div>
              <div>
                <label style={S.label}>Last name</label>
                <Inp icon={<User size={14} color="#94a3b8"/>} value={form.last_name}
                  onChange={e=>set('last_name',e.target.value)} placeholder="Sharma" required/>
              </div>
            </div>

            {/* Email */}
            <div style={{marginBottom:16}}>
              <label style={S.label}>Email address</label>
              <Inp icon={<Mail size={14} color="#94a3b8"/>} type="email" required
                value={form.email} onChange={e=>set('email',e.target.value)} placeholder="you@hospital.com"/>
            </div>

            {/* Password */}
            <div style={{marginBottom:6}}>
              <label style={S.label}>Password</label>
              <div style={{position:'relative'}}>
                <span style={S.icoLeft}><Lock size={14} color="#94a3b8"/></span>
                <input type={showPw?'text':'password'} required minLength={8}
                  value={form.password} onChange={e=>set('password',e.target.value)}
                  placeholder="Min. 8 characters"
                  style={{...S.inp, paddingRight:44}}
                  onFocus={focusOn} onBlur={focusOff}/>
                <button type="button" onClick={()=>setShowPw(s=>!s)} style={S.eyeBtn} aria-label="toggle">
                  {showPw ? <EyeOff size={14} color="#94a3b8"/> : <Eye size={14} color="#94a3b8"/>}
                </button>
              </div>
            </div>

            {/* Strength bar */}
            {form.password && (
              <div style={{marginBottom:16}}>
                <div style={{display:'flex',gap:4,marginBottom:4}}>
                  {[1,2,3,4].map(n=>(
                    <div key={n} style={{flex:1,height:3,borderRadius:2,
                      background: n<=pwStr ? strColor[pwStr] : '#e2e8f0',
                      transition:'background .3s'}}/>
                  ))}
                </div>
                <span style={{fontSize:11.5,color:strColor[pwStr],fontWeight:600}}>{strLabel[pwStr]}</span>
              </div>
            )}

            {/* Phone + Hospital */}
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14,marginBottom:16}}>
              <div>
                <label style={S.label}>Phone <span style={{color:'#94a3b8',fontWeight:400}}>(optional)</span></label>
                <Inp icon={<Phone size={14} color="#94a3b8"/>} type="tel"
                  value={form.phone} onChange={e=>set('phone',e.target.value)} placeholder="+91 98765…"/>
              </div>
              <div>
                <label style={S.label}>Hospital slug</label>
                <Inp icon={<Building2 size={14} color="#94a3b8"/>}
                  value={form.hospital_slug} onChange={e=>set('hospital_slug',e.target.value)} placeholder="default"/>
              </div>
            </div>

            {/* Patient notice */}
            <div style={{ marginBottom: 20, padding: '10px 14px', borderRadius: 10, background: '#f0fdfa', border: '1px solid #ccfbf1', display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 18 }}>🧑‍⚕️</span>
              <div style={{ fontSize: 12, color: '#0f766e', lineHeight: 1.4 }}>
                <strong>Patient Registration:</strong> Self-registration creates a patient account. Doctor and staff credentials are administrator-provisioned.
              </div>
            </div>

            <button type="submit" disabled={loading}
              style={{...S.submitBtn, opacity:loading?.75:1, cursor:loading?'not-allowed':'pointer'}}
              onMouseEnter={e=>{if(!loading)e.currentTarget.style.background='linear-gradient(135deg,#1d4ed8,#1e40af)'}}
              onMouseLeave={e=>{e.currentTarget.style.background='linear-gradient(135deg,#2563eb,#1d4ed8)'}}>
              {loading
                ? <><span style={S.spinner}/> Creating account…</>
                : <>Create Account <ArrowRight size={15}/></>}
            </button>
          </form>

          <p style={S.switchTxt}>
            Already have an account?{' '}
            <Link to="/login" style={S.switchLink}>Sign in</Link>
          </p>
          <Link to="/" style={S.backLink}>← Back to home</Link>
        </div>
      </div>
    </div>
  )
}

/* ── simple input helper ── */
function Inp({ icon, ...props }) {
  return (
    <div style={{position:'relative'}}>
      <span style={S.icoLeft}>{icon}</span>
      <input {...props} style={S.inp} onFocus={focusOn} onBlur={focusOff}/>
    </div>
  )
}
const focusOn  = e => { e.target.style.borderColor = '#2563eb' }
const focusOff = e => { e.target.style.borderColor = '#e2e8f0' }

const S = {
  page:      { minHeight:'100vh', display:'flex', fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif" },
  left:      { flex:'0 0 44%', background:'linear-gradient(135deg,#0A1628 0%,#0d2040 55%,#0f2750 100%)', position:'relative', overflow:'hidden', display:'flex', alignItems:'center', padding:'2.5rem 3rem' },
  gridBg:    { position:'absolute', inset:0, backgroundImage:'linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px)', backgroundSize:'40px 40px', pointerEvents:'none' },
  glow1:     { position:'absolute', top:'15%', left:'5%',  width:300, height:300, background:'#2563eb', borderRadius:'50%', filter:'blur(110px)', opacity:.11, pointerEvents:'none' },
  glow2:     { position:'absolute', bottom:'10%', right:'0%', width:240, height:240, background:'#00C6A7', borderRadius:'50%', filter:'blur(100px)', opacity:.08, pointerEvents:'none' },
  logoRow:   { display:'flex', alignItems:'center', gap:10, marginBottom:30 },
  logoIcon:  { width:36, height:36, borderRadius:10, background:'linear-gradient(135deg,#2563eb,#00C6A7)', display:'flex', alignItems:'center', justifyContent:'center', boxShadow:'0 4px 16px rgba(37,99,235,.4)' },
  logoText:  { fontWeight:800, fontSize:'1.1rem', color:'#fff', letterSpacing:-0.5 },
  leftH1:    { fontSize:'clamp(1.7rem,2.8vw,2.4rem)', fontWeight:800, color:'#fff', lineHeight:1.15, letterSpacing:-1, marginBottom:12 },
  grad:      { background:'linear-gradient(135deg,#93c5fd,#00C6A7)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent', backgroundClip:'text' },
  leftSub:   { fontSize:'0.88rem', color:'#94a3b8', lineHeight:1.75, maxWidth:360, marginBottom:24 },
  right:     { flex:1, display:'flex', alignItems:'center', justifyContent:'center', padding:'1.5rem', background:'#F7FAFF', overflowY:'auto' },
  card:      { width:'100%', maxWidth:440, background:'#fff', borderRadius:20, padding:'2.2rem 2.4rem', boxShadow:'0 8px 40px rgba(0,0,0,.08)', border:'1px solid #f1f5f9' },
  mobileLogo:{ display:'none', alignItems:'center', gap:9, marginBottom:20 },
  cardTitle: { fontSize:'1.45rem', fontWeight:800, color:'#0A1628', letterSpacing:-0.5, marginBottom:5 },
  cardSub:   { fontSize:'0.86rem', color:'#64748b', marginBottom:22, lineHeight:1.5 },
  label:     { display:'block', fontSize:13, fontWeight:600, color:'#374151', marginBottom:6 },
  icoLeft:   { position:'absolute', left:13, top:'50%', transform:'translateY(-50%)', pointerEvents:'none', display:'flex', zIndex:1 },
  inp:       { width:'100%', padding:'10px 14px 10px 38px', border:'1.5px solid #e2e8f0', borderRadius:10, fontSize:13.5, color:'#0f172a', background:'#fff', outline:'none', transition:'border-color .2s', boxSizing:'border-box' },
  eyeBtn:    { position:'absolute', right:0, top:0, bottom:0, background:'none', border:'none', cursor:'pointer', padding:'0 12px', display:'flex', alignItems:'center' },
  submitBtn: { width:'100%', padding:'12px', borderRadius:11, border:'none', background:'linear-gradient(135deg,#2563eb,#1d4ed8)', color:'#fff', fontWeight:700, fontSize:'0.925rem', fontFamily:'inherit', boxShadow:'0 6px 20px rgba(37,99,235,.35)', transition:'all .2s', display:'flex', alignItems:'center', justifyContent:'center', gap:8 },
  spinner:   { width:15, height:15, border:'2px solid rgba(255,255,255,.3)', borderTop:'2px solid #fff', borderRadius:'50%', display:'inline-block', animation:'spin .7s linear infinite' },
  switchTxt: { textAlign:'center', marginTop:20, fontSize:13, color:'#6b7280' },
  switchLink:{ color:'#2563eb', fontWeight:600, textDecoration:'none' },
  backLink:  { display:'block', textAlign:'center', marginTop:12, fontSize:12.5, color:'#94a3b8', textDecoration:'none' },
}

const css = `
  @keyframes spin { to { transform: rotate(360deg); } }
  @media (max-width: 768px) {
    .auth-left        { display: none !important; }
    .auth-mobile-logo { display: flex !important; }
  }
`
