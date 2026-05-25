import { useState, useRef, useEffect } from 'react'
import { aiApi } from '../services/api'
import toast from 'react-hot-toast'

const URGENCY = { low:{bg:'#dcfce7',color:'#15803d',label:'🟢 Low'}, medium:{bg:'#fef3c7',color:'#b45309',label:'🟡 Medium'}, high:{bg:'#fee2e2',color:'#b91c1c',label:'🔴 High'}, emergency:{bg:'#dc2626',color:'#fff',label:'🚨 EMERGENCY'} }

function SymptomChecker() {
  const [input, setInput] = useState(''); const [symptoms, setSymptoms] = useState([])
  const [form, setForm] = useState({ age:'', gender:'', medical_history:'' })
  const [result, setResult] = useState(null); const [loading, setLoading] = useState(false)

  const add = () => { const s=input.trim(); if(s && !symptoms.includes(s)){ setSymptoms(p=>[...p,s]); setInput('') } }

  const analyze = async () => {
    if (!symptoms.length) return toast.error('Add at least one symptom')
    setLoading(true)
    try {
      const r = await aiApi.analyzeSymptoms({ symptoms, age: form.age ? +form.age : null, gender: form.gender||null, medical_history: form.medical_history||null })
      setResult(r.data)
    } catch(err) { toast.error(err.response?.data?.detail || 'Analysis failed') }
    finally { setLoading(false) }
  }

  const u = result ? URGENCY[result.urgency_level] : null

  return (
    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20 }}>
      <div className="card">
        <div className="card-header"><span className="card-title">🩺 Symptom Checker</span></div>
        <div className="card-body">
          <div className="form-group">
            <label className="form-label">Add Symptoms</label>
            <div style={{ display:'flex', gap:8 }}>
              <input className="form-control" value={input} onChange={e=>setInput(e.target.value)}
                onKeyDown={e=>e.key==='Enter'&&(e.preventDefault(),add())} placeholder="e.g. chest pain..." />
              <button className="btn btn-primary btn-sm" onClick={add}>Add</button>
            </div>
          </div>
          {symptoms.length > 0 && (
            <div style={{ display:'flex', flexWrap:'wrap', gap:8, marginBottom:16 }}>
              {symptoms.map(s=>(
                <span key={s} style={{ background:'#eff6ff', color:'#2563eb', padding:'4px 10px', borderRadius:20, fontSize:12, fontWeight:500, display:'flex', alignItems:'center', gap:6 }}>
                  {s}
                  <button onClick={()=>setSymptoms(p=>p.filter(x=>x!==s))} style={{background:'none',border:'none',color:'#93c5fd',cursor:'pointer',padding:0}}>✕</button>
                </span>
              ))}
            </div>
          )}
          <div className="form-row">
            <div className="form-group"><label className="form-label">Age</label><input type="number" className="form-control" value={form.age} onChange={e=>setForm(p=>({...p,age:e.target.value}))} placeholder="35" /></div>
            <div className="form-group"><label className="form-label">Gender</label>
              <select className="form-control" value={form.gender} onChange={e=>setForm(p=>({...p,gender:e.target.value}))}>
                <option value="">Select...</option><option value="male">Male</option><option value="female">Female</option><option value="other">Other</option>
              </select>
            </div>
          </div>
          <div className="form-group"><label className="form-label">Medical History (optional)</label>
            <textarea className="form-control" rows={2} value={form.medical_history} onChange={e=>setForm(p=>({...p,medical_history:e.target.value}))} placeholder="Diabetes, hypertension..." />
          </div>
          <button className="btn btn-primary w-full" onClick={analyze} disabled={loading||!symptoms.length} style={{justifyContent:'center',marginTop:4}}>
            {loading ? '🤖 Analyzing...' : '🔍 Analyze Symptoms'}
          </button>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">🤖 AI Results</span></div>
        <div className="card-body">
          {!result ? (
            <div className="empty-state" style={{padding:'32px 20px'}}>
              <div style={{fontSize:48}}>🤖</div>
              <p style={{marginTop:12}}>Add symptoms and click Analyze</p>
              <p style={{fontSize:11,color:'#9ca3af',marginTop:8}}>Powered by Claude AI</p>
            </div>
          ) : (
            <div>
              <div style={{ background:u?.bg, color:u?.color, padding:'10px 14px', borderRadius:8, marginBottom:16, fontWeight:700, fontSize:14, textAlign:'center' }}>Urgency: {u?.label}</div>
              <div style={{ background:'#eff6ff', borderRadius:8, padding:'12px 14px', marginBottom:16 }}>
                <div style={{fontSize:11,color:'#6b7280',fontWeight:600,marginBottom:4}}>RECOMMENDED SPECIALIST</div>
                <div style={{fontSize:15,fontWeight:700,color:'#1d4ed8'}}>👨‍⚕️ {result.recommended_specialist}</div>
              </div>
              <div style={{marginBottom:16}}>
                <div style={{fontSize:12,fontWeight:600,color:'#374151',marginBottom:8}}>POSSIBLE CONDITIONS</div>
                {result.suggested_conditions.map((c,i)=>(
                  <div key={i} style={{border:'1px solid #e5e7eb',borderRadius:6,padding:'10px 12px',marginBottom:8}}>
                    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                      <span style={{fontWeight:500,fontSize:13}}>{c.name}</span>
                      <span className={`badge ${c.probability==='high'?'badge-red':c.probability==='medium'?'badge-yellow':'badge-gray'}`}>{c.probability}</span>
                    </div>
                    {c.description&&<div style={{fontSize:12,color:'#6b7280',marginTop:4}}>{c.description}</div>}
                  </div>
                ))}
              </div>
              <div style={{background:'#f0fdf4',borderRadius:8,padding:'12px 14px',marginBottom:12}}>
                <div style={{fontSize:11,fontWeight:600,color:'#15803d',marginBottom:4}}>ADVICE</div>
                <div style={{fontSize:13}}>{result.advice}</div>
              </div>
              <div style={{fontSize:11,color:'#9ca3af',fontStyle:'italic'}}>⚠️ {result.disclaimer}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Chatbot() {
  const [msgs, setMsgs] = useState([{ role:'ai', text:"Hello! I'm your hospital assistant. Ask me about appointments, doctors, or general health queries." }])
  const [input, setInput] = useState(''); const [loading, setLoading] = useState(false); const [convId, setConvId] = useState(null)
  const bottom = useRef()

  useEffect(() => { bottom.current?.scrollIntoView({ behavior:'smooth' }) }, [msgs])

  const send = async () => {
    const text = input.trim(); if (!text || loading) return
    setInput(''); setMsgs(p=>[...p,{role:'user',text}]); setLoading(true)
    try {
      const r = await aiApi.chat(text, convId)
      setConvId(r.data.conversation_id)
      setMsgs(p=>[...p,{role:'ai',text:r.data.reply}])
    } catch { setMsgs(p=>[...p,{role:'ai',text:"Sorry, I'm having trouble. Please try again."}]) }
    finally { setLoading(false) }
  }

  return (
    <div className="card chat-container">
      <div className="card-header"><span className="card-title">💬 Patient Assistant</span><span className="badge badge-green">● Online</span></div>
      <div className="chat-messages">
        {msgs.map((m,i)=>(<div key={i} className={`chat-bubble ${m.role}`}>{m.text}</div>))}
        {loading && <div className="chat-bubble ai">●●●</div>}
        <div ref={bottom} />
      </div>
      <div style={{ padding:'0 16px 8px', display:'flex', flexWrap:'wrap', gap:6 }}>
        {msgs.length === 1 && ['Book appointment','Find a cardiologist','Emergency contact','Visiting hours'].map(q=>(
          <button key={q} className="btn btn-secondary btn-sm" onClick={() => { setInput(q); setTimeout(send, 50) }}>{q}</button>
        ))}
      </div>
      <div className="chat-input-row">
        <textarea className="chat-input" rows={1} value={input} onChange={e=>setInput(e.target.value)}
          onKeyDown={e=>e.key==='Enter'&&!e.shiftKey&&(e.preventDefault(),send())} placeholder="Type a message..." />
        <button className="btn btn-primary" onClick={send} disabled={loading||!input.trim()}>Send</button>
      </div>
    </div>
  )
}

export default function AIAssistant() {
  const [tab, setTab] = useState('symptom')
  return (
    <div>
      <div style={{ display:'flex', gap:8, marginBottom:20 }}>
        <button className={`btn ${tab==='symptom'?'btn-primary':'btn-secondary'}`} onClick={()=>setTab('symptom')}>🩺 Symptom Checker</button>
        <button className={`btn ${tab==='chat'?'btn-primary':'btn-secondary'}`} onClick={()=>setTab('chat')}>💬 AI Chatbot</button>
      </div>
      {tab==='symptom' ? <SymptomChecker /> : <Chatbot />}
      <div style={{ marginTop:16, padding:'12px 16px', background:'#fef3c7', borderRadius:8, fontSize:12, color:'#92400e' }}>
        ⚠️ <strong>Disclaimer:</strong> AI suggestions are informational only. Always consult a qualified healthcare professional.
      </div>
    </div>
  )
}
