import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Sidebar() {
    const { user, logout, hasRole } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const navItems = [
        { to: '/', icon: '📊', label: 'Dashboard', roles: ['student', 'engineer', 'admin'] },
        { to: '/troubleshoot', icon: '🔍', label: 'Troubleshoot', roles: ['student', 'engineer', 'admin'] },
        { to: '/learn', icon: '📚', label: 'Learning Mode', roles: ['student', 'engineer', 'admin'] },
        { to: '/scenarios', icon: '🧪', label: 'Scenarios', roles: ['student', 'engineer', 'admin'] },
        { to: '/health', icon: '💚', label: 'Health Score', roles: ['student', 'engineer', 'admin'] },
        { to: '/reports', icon: '📄', label: 'Reports', roles: ['student', 'engineer', 'admin'] },
        { to: '/admin', icon: '⚙️', label: 'Admin', roles: ['admin'] },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <div className="logo-icon">🌐</div>
                <h1>
                    NetAssist
                    <span>Packet Tracer MCP</span>
                </h1>
            </div>

            <nav className="sidebar-nav">
                {navItems
                    .filter((item) => hasRole(...item.roles))
                    .map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            end={item.to === '/'}
                            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                        >
                            <span className="nav-icon">{item.icon}</span>
                            {item.label}
                        </NavLink>
                    ))}
            </nav>

            <div className="sidebar-footer">
                <div className="user-info">
                    <div className="user-avatar">
                        {user?.username?.[0]?.toUpperCase() || '?'}
                    </div>
                    <div className="user-details">
                        <div className="name">{user?.username}</div>
                        <div className="role">{user?.role}</div>
                    </div>
                </div>
                <button onClick={handleLogout} className="nav-link" style={{ marginTop: 8, color: '#ef4444' }}>
                    <span className="nav-icon">🚪</span>
                    Logout
                </button>
            </div>
        </aside>
    );
}
