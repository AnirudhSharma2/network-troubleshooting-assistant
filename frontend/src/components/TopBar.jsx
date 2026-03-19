import { useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const PAGE_META = {
    '/dashboard': { title: 'Dashboard', crumb: ['Dashboard'] },
    '/troubleshoot': { title: 'Troubleshoot', crumb: ['Workspace', 'Troubleshoot'] },
    '/learn': { title: 'Learning Mode', crumb: ['Workspace', 'Learning'] },
    '/scenarios': { title: 'Practice Scenarios', crumb: ['Workspace', 'Scenarios'] },
    '/health': { title: 'Health Score', crumb: ['Workspace', 'Health Score'] },
    '/reports': { title: 'Reports', crumb: ['Workspace', 'Reports'] },
    '/admin': { title: 'Admin Panel', crumb: ['Admin', 'User Management'] },
};

export default function TopBar() {
    const { user } = useAuth();
    const location = useLocation();
    const meta = PAGE_META[location.pathname] || { title: 'NetAssist', crumb: [] };

    return (
        <header className="topbar">
            <div className="topbar-left">
                <div className="topbar-breadcrumb">
                    <Link to="/" className="topbar-breadcrumb-home" aria-label="Dashboard">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                            <polyline points="9 22 9 12 15 12 15 22"/>
                        </svg>
                    </Link>
                    {meta.crumb.map((c, i) => (
                        <span key={i} className="topbar-breadcrumb-item">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="m9 18 6-6-6-6"/>
                            </svg>
                            {c}
                        </span>
                    ))}
                </div>
            </div>
            <div className="topbar-right">
                <Link to="/troubleshoot" className="topbar-action-btn">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                    </svg>
                    New Analysis
                </Link>
                <div className="topbar-user">
                    <div className="topbar-avatar">
                        {user?.username?.[0]?.toUpperCase() || '?'}
                    </div>
                    <div className="topbar-user-info">
                        <span className="topbar-username">{user?.username}</span>
                        <span className="topbar-role">{user?.role}</span>
                    </div>
                </div>
            </div>
        </header>
    );
}
