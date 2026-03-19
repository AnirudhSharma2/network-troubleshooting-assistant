import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/* ── SVG Icon Components ─────────────────────────────────────── */
const IconDashboard = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
        <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
    </svg>
);
const IconSearch = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
    </svg>
);
const IconBook = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
    </svg>
);
const IconFlask = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 3h6l1 9H8L9 3z"/><path d="M6.8 21a7 7 0 0 1 10.4 0"/><line x1="12" y1="12" x2="12" y2="21"/>
    </svg>
);
const IconActivity = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>
);
const IconFile = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
    </svg>
);
const IconSettings = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
    </svg>
);
const IconLogout = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
        <polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
    </svg>
);
const IconNetwork = () => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2"/>
        <path d="M8 21h8"/><path d="M12 17v4"/>
    </svg>
);

/* ── Nav config ─────────────────────────────────────────────── */
const NAV_ITEMS = [
    { to: '/dashboard', icon: <IconDashboard />, label: 'Dashboard', roles: ['student', 'engineer', 'admin'] },
    { to: '/troubleshoot', icon: <IconSearch />, label: 'Troubleshoot', roles: ['student', 'engineer', 'admin'] },
    { to: '/learn', icon: <IconBook />, label: 'Learning Mode', roles: ['student', 'engineer', 'admin'] },
    { to: '/scenarios', icon: <IconFlask />, label: 'Scenarios', roles: ['student', 'engineer', 'admin'] },
    { to: '/health', icon: <IconActivity />, label: 'Health Score', roles: ['student', 'engineer', 'admin'] },
    { to: '/reports', icon: <IconFile />, label: 'Reports', roles: ['student', 'engineer', 'admin'] },
    { to: '/admin', icon: <IconSettings />, label: 'Admin', roles: ['admin'] },
];

export default function Sidebar() {
    const { user, logout, hasRole } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    return (
        <aside className="sidebar">
            {/* Brand */}
            <div className="sidebar-logo">
                <div className="logo-icon">
                    <IconNetwork />
                </div>
                <h1>
                    NetAssist
                    <span>Packet Tracer</span>
                </h1>
            </div>

            {/* Navigation */}
            <nav className="sidebar-nav">
                <div className="sidebar-nav-section-label">Workspace</div>
                {NAV_ITEMS
                    .filter((item) => item.roles.some((r) => hasRole(r)))
                    .map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            end={item.to === '/dashboard'}
                            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
                        >
                            <span className="nav-icon">{item.icon}</span>
                            {item.label}
                        </NavLink>
                    ))}
            </nav>

            {/* Footer */}
            <div className="sidebar-footer">
                <div className="user-card">
                    <div className="user-avatar">
                        {user?.username?.[0]?.toUpperCase() || '?'}
                    </div>
                    <div className="user-details">
                        <div className="name">{user?.username}</div>
                        <div className="role">{user?.role}</div>
                    </div>
                </div>
                <button onClick={handleLogout} className="nav-link logout-btn">
                    <span className="nav-icon"><IconLogout /></span>
                    Sign out
                </button>
            </div>
        </aside>
    );
}
