import { useQuery } from 'react-query'
import { analyticsApi, appointmentApi } from '../services/api'
import useAuthStore from '../store/authStore'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

function StatCard({ label, value, icon, color = '#2563eb' }) {
  return (
    <div className="stat-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="stat-label">{label}</div>
          <div className="stat-value" style={{ color }}>{value ?? '—'}</div>
        </div>
        <span style={{ fontSize: 28, opacity: .5 }}>{icon}</span>
      </div>
    </div>
  )
}

const STATUS_BADGE = {
  pending: 'badge-yellow', confirmed: 'badge-blue',
  completed: 'badge-green', cancelled: 'badge-red', no_show: 'badge-gray',
}

export default function Dashboard() {
  const { user } = useAuthStore()
  const isAdmin = ['admin', 'super_admin'].includes(user?.role)
  const today = new Date().toISOString().split('T')[0]

  const { data: summary } = useQuery('summary', () => analyticsApi.summary().then(r => r.data), { enabled: isAdmin })
  const { data: trends } = useQuery('trends', () => analyticsApi.trends(30).then(r => r.data), { enabled: isAdmin })
  const { data: todayAppts } = useQuery('today', () =>
    appointmentApi.list({ date_from: today, date_to: today, page_size: 10 }).then(r => r.data)
  )

  const chartData = (trends || []).map(t => ({
    date: t.date.slice(5), count: t.count,
  }))

  const greeting = () => {
    const h = new Date().getHours()
    return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening'
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 20, fontWeight: 700 }}>{greeting()}, {user?.first_name} 👋</h2>
        <p className="text-muted" style={{ marginTop: 4 }}>
          {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>

      {isAdmin && summary && (
        <div className="stat-grid">
          <StatCard label="Total Patients"      value={summary.total_patients}            icon="🧑‍🤝‍🧑" />
          <StatCard label="Total Doctors"       value={summary.total_doctors}             icon="👨‍⚕️" />
          <StatCard label="Today"               value={summary.appointments_today}        icon="📅" color="#16a34a" />
          <StatCard label="This Month"          value={summary.appointments_this_month}   icon="📆" />
          <StatCard label="Pending"             value={summary.pending_appointments}      icon="⏳" color="#d97706" />
          <StatCard label="Revenue (Month)"     value={`₹${(summary.revenue_this_month||0).toLocaleString()}`} icon="💰" color="#7c3aed" />
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: isAdmin && chartData.length ? '1.4fr 1fr' : '1fr', gap: 20 }}>
        {isAdmin && chartData.length > 0 && (
          <div className="card">
            <div className="card-header"><span className="card-title">📈 Appointments — Last 30 Days</span></div>
            <div className="card-body" style={{ paddingTop: 8 }}>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} interval={4} />
                  <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#2563eb" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        <div className="card">
          <div className="card-header">
            <span className="card-title">📋 Today's Appointments</span>
            <span className="badge badge-blue">{todayAppts?.total || 0}</span>
          </div>
          {!todayAppts?.items?.length ? (
            <div className="empty-state"><p>No appointments today</p></div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Time</th><th>Name</th><th>Priority</th><th>Status</th></tr></thead>
                <tbody>
                  {todayAppts.items.map(a => (
                    <tr key={a.id}>
                      <td style={{ fontWeight: 600 }}>{a.time_slot}</td>
                      <td style={{ fontSize: 12 }}>
                        {user?.role === 'patient'
                          ? `Dr. ${a.doctor?.user?.first_name || ''} ${a.doctor?.user?.last_name || ''}`
                          : `${a.patient?.user?.first_name || ''} ${a.patient?.user?.last_name || ''}`}
                      </td>
                      <td>
                        <span className={`badge ${a.priority === 'emergency' ? 'badge-red' : a.priority === 'urgent' ? 'badge-yellow' : 'badge-gray'}`}>
                          {a.priority}
                        </span>
                      </td>
                      <td><span className={`badge ${STATUS_BADGE[a.status] || 'badge-gray'}`}>{a.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
