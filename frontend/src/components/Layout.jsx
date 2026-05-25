import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import useAuthStore from '../store/authStore'
import { notificationApi } from '../services/api'

const NAV = [
  { to: '/dashboard',    label: 'Dashboard',       icon: '⊞', roles: ['admin','super_admin','doctor','patient'] },
  { to: '/appointments', label: 'Appointments',    icon: '📅', roles: ['admin','super_admin','doctor','patient'] },
  { to: '/doctors',      label: 'Doctors',         icon: '👨‍⚕️', roles: ['admin','super_admin','patient'] },
  { to: '/patients',     label: 'Patients',        icon: '🧑‍🤝‍🧑', roles: ['admin','super_admin','doctor'] },
  { to: '/records',      label: 'Medical Records', icon: '📁', roles: ['admin','super_admin','doctor','patient'] },
  { to: '/analytics',   label: 'Analytics',       icon: '📊', roles: ['admin','super_admin'] },
  { to: '/ai',           label: 'AI Assistant',    icon: '🤖', roles: ['admin','super_admin','doctor','patient'] },
  { to: '/audit',        label: 'Audit Logs',      icon: '🛡️', roles: ['admin','super_admin'] },
]

const PAGE_TITLES = {
  '/dashboard': 'Dashboard', '/appointments': 'Appointments', '/doctors': 'Doctors',
  '/patients': 'Patients', '/records': 'Medical Records', '/analytics': 'Analytics',
  '/ai': 'AI Assistant', '/audit': 'Audit Logs', '/profile': 'My Profile',
}

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [unread, setUnread] = useState(0)

  useEffect(() => {
    notificationApi.list().then(r => {
      setUnread(r.data.filter(n => !n.is_read).length)
    }).catch(() => {})
  }, [location.pathname])

  const handleLogout = async () => { await logout(); navigate('/login') }
  const items = NAV.filter(n => n.roles.includes(user?.role))
  const initials = user ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase() : '?'
  const pageTitle = PAGE_TITLES[location.pathname] || 'MediCore HMS'

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>🏥 MediCore HMS</h1>
          <span>Hospital Management System</span>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Navigation</div>
          {items.map(item => (
            <NavLink key={item.to} to={item.to}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              <span>{item.icon}</span> {item.label}
            </NavLink>
          ))}

          <div className="nav-section-label" style={{ marginTop: 12 }}>Account</div>
          <NavLink to="/profile" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
            <span>👤</span> Profile
          </NavLink>
          <button className="nav-link" onClick={handleLogout}>
            <span>🚪</span> Sign Out
          </button>
        </nav>

        <div className="sidebar-user">
          <div className="avatar">{initials}</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="sidebar-user-name">{user?.first_name} {user?.last_name}</div>
            <div className="sidebar-user-role">{user?.role?.replace('_', ' ')}</div>
          </div>
        </div>
      </aside>

      <div className="main-content">
        <header className="topbar">
          <span className="topbar-title">{pageTitle}</span>
          <div className="topbar-actions">
            <button className="notif-btn" title="Notifications">
              🔔
              {unread > 0 && <span className="notif-dot" />}
            </button>
            <div className="avatar" style={{ cursor: 'pointer' }} onClick={() => navigate('/profile')}>
              {initials}
            </div>
          </div>
        </header>
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
