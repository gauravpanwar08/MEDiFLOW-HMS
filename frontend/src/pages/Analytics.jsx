import { useQuery } from 'react-query'
import { analyticsApi } from '../services/api'
import { BarChart,Bar,XAxis,YAxis,Tooltip,ResponsiveContainer,CartesianGrid,LineChart,Line,PieChart,Pie,Cell,Legend } from 'recharts'

const COLORS = ['#2563eb','#16a34a','#dc2626','#d97706','#7c3aed']

function Stat({ label, value, icon, color='#2563eb' }) {
  return (
    <div className="stat-card">
      <div style={{ display:'flex', justifyContent:'space-between' }}>
        <div><div className="stat-label">{label}</div><div className="stat-value" style={{color}}>{value ?? '—'}</div></div>
        <span style={{ fontSize:32, opacity:.4 }}>{icon}</span>
      </div>
    </div>
  )
}

export default function Analytics() {
  const { data: s, isLoading } = useQuery('analytics-summary', () => analyticsApi.summary().then(r => r.data))
  const { data: trends } = useQuery('analytics-trends', () => analyticsApi.trends(30).then(r => r.data))
  const { data: workloads } = useQuery('analytics-workloads', () => analyticsApi.workloads().then(r => r.data))

  const chartData = (trends||[]).map(t => ({ date: t.date.slice(5), count: t.count }))
  const pie = s ? [
    { name:'Pending', value: s.pending_appointments },
    { name:'Completed', value: s.completed_appointments },
    { name:'Cancelled', value: s.cancelled_appointments },
  ].filter(d => d.value > 0) : []

  if (isLoading) return <div className="loading"><div className="spinner" /></div>

  return (
    <div>
      <div className="stat-grid">
        <Stat label="Total Patients"    value={s?.total_patients}          icon="🧑‍🤝‍🧑" />
        <Stat label="Total Doctors"     value={s?.total_doctors}           icon="👨‍⚕️" />
        <Stat label="This Month"        value={s?.appointments_this_month} icon="📅" />
        <Stat label="Revenue (Month)"   value={`₹${(s?.revenue_this_month||0).toLocaleString()}`} icon="💰" color="#7c3aed" />
        <Stat label="Pending"           value={s?.pending_appointments}    icon="⏳" color="#d97706" />
        <Stat label="Completed"         value={s?.completed_appointments}  icon="✅" color="#16a34a" />
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'2fr 1fr', gap:20, marginBottom:20 }}>
        <div className="card">
          <div className="card-header"><span className="card-title">📈 Daily Appointments (30 days)</span></div>
          <div className="card-body" style={{ paddingTop:8 }}>
            {chartData.length ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" tick={{fontSize:11}} tickLine={false} interval={4} />
                  <YAxis tick={{fontSize:11}} tickLine={false} axisLine={false} />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="#2563eb" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : <div className="empty-state"><p>No trend data</p></div>}
          </div>
        </div>
        <div className="card">
          <div className="card-header"><span className="card-title">📊 Status Breakdown</span></div>
          <div className="card-body" style={{ display:'flex', justifyContent:'center' }}>
            {pie.length ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={pie} cx="50%" cy="50%" innerRadius={55} outerRadius={80} dataKey="value" paddingAngle={3}>
                    {pie.map((_,i) => <Cell key={i} fill={COLORS[i]} />)}
                  </Pie>
                  <Tooltip /><Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : <div className="empty-state"><p>No data</p></div>}
          </div>
        </div>
      </div>

      {workloads?.length > 0 && (
        <div className="card">
          <div className="card-header"><span className="card-title">👨‍⚕️ Doctor Workload (This Month)</span></div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Doctor</th><th>Specialty</th><th>Total</th><th>Done</th><th>Pending</th><th>Rating</th></tr></thead>
              <tbody>
                {workloads.map(w => (
                  <tr key={w.doctor_id}>
                    <td style={{fontWeight:500}}>{w.doctor_name}</td>
                    <td style={{fontSize:12}}>{w.specialty}</td>
                    <td><strong>{w.total_appointments}</strong></td>
                    <td><span className="badge badge-green">{w.completed}</span></td>
                    <td><span className="badge badge-yellow">{w.pending}</span></td>
                    <td>⭐ {w.avg_rating?.toFixed(1)||'—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={workloads.slice(0,8)} margin={{left:-20}}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="doctor_name" tick={{fontSize:10}} tickLine={false} tickFormatter={n => n.split(' ')[0]} />
                <YAxis tick={{fontSize:11}} tickLine={false} axisLine={false} />
                <Tooltip /><Legend />
                <Bar dataKey="completed" name="Completed" stackId="a" fill="#16a34a" />
                <Bar dataKey="pending"   name="Pending"   stackId="a" fill="#d97706" />
                <Bar dataKey="cancelled" name="Cancelled" stackId="a" fill="#dc2626" radius={[3,3,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  )
}
