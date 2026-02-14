import { useState, useEffect } from 'react';
import { adminAPI } from '../services/api';

export default function AdminPage() {
    const [users, setUsers] = useState([]);
    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            adminAPI.listUsers(),
            adminAPI.getAnalytics(),
        ])
            .then(([usersRes, analyticsRes]) => {
                setUsers(usersRes.data);
                setAnalytics(analyticsRes.data);
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const handleRoleChange = async (userId, newRole) => {
        try {
            await adminAPI.updateRole(userId, { role: newRole });
            setUsers((prev) =>
                prev.map((u) => (u.id === userId ? { ...u, role: newRole } : u))
            );
        } catch (err) {
            console.error(err);
        }
    };

    const handleDelete = async (userId) => {
        if (!window.confirm('Delete this user? This cannot be undone.')) return;
        try {
            await adminAPI.deleteUser(userId);
            setUsers((prev) => prev.filter((u) => u.id !== userId));
        } catch (err) {
            console.error(err);
        }
    };

    if (loading) return <div className="loading"><div className="spinner"></div></div>;

    return (
        <div className="fade-in">
            <div className="page-header">
                <h2>Admin Panel</h2>
                <p>Manage users, roles, and view system-wide analytics.</p>
            </div>

            {/* Analytics Cards */}
            {analytics && (
                <div className="card-grid" style={{ marginBottom: 24 }}>
                    <div className="stat-card">
                        <div className="stat-icon primary">👥</div>
                        <div>
                            <div className="stat-value">{analytics.total_users}</div>
                            <div className="stat-label">Total Users</div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon success">📊</div>
                        <div>
                            <div className="stat-value">{analytics.total_analyses}</div>
                            <div className="stat-label">Total Analyses</div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon warning">💯</div>
                        <div>
                            <div className="stat-value">{analytics.average_score}</div>
                            <div className="stat-label">Average Score</div>
                        </div>
                    </div>
                </div>
            )}

            {/* Role Distribution */}
            {analytics?.users_by_role && (
                <div className="card" style={{ marginBottom: 24 }}>
                    <div className="card-header"><h3>Role Distribution</h3></div>
                    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                        {Object.entries(analytics.users_by_role).map(([role, count]) => (
                            <div key={role} style={{
                                background: 'var(--bg-glass)', border: '1px solid var(--border-default)',
                                borderRadius: 'var(--radius-sm)', padding: '12px 20px',
                                textAlign: 'center', minWidth: 120
                            }}>
                                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--accent-primary)' }}>{count}</div>
                                <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'capitalize' }}>{role}s</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* User Management */}
            <div className="card">
                <div className="card-header">
                    <h3>👥 User Management</h3>
                </div>
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Username</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Joined</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map((u) => (
                                <tr key={u.id}>
                                    <td>{u.id}</td>
                                    <td style={{ fontWeight: 600 }}>{u.username}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{u.email}</td>
                                    <td>
                                        <select
                                            className="role-select"
                                            value={u.role}
                                            onChange={(e) => handleRoleChange(u.id, e.target.value)}
                                        >
                                            <option value="student">Student</option>
                                            <option value="engineer">Engineer</option>
                                            <option value="admin">Admin</option>
                                        </select>
                                    </td>
                                    <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}
                                    </td>
                                    <td>
                                        <button
                                            onClick={() => handleDelete(u.id)}
                                            className="btn btn-sm btn-danger"
                                        >
                                            🗑️ Delete
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Recent Activity */}
            {analytics?.recent_activity?.length > 0 && (
                <div className="card" style={{ marginTop: 24 }}>
                    <div className="card-header"><h3>📋 Recent Activity</h3></div>
                    <div className="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>User</th>
                                    <th>Analysis</th>
                                    <th>Score</th>
                                    <th>Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                {analytics.recent_activity.map((a, i) => (
                                    <tr key={i}>
                                        <td style={{ fontWeight: 600 }}>{a.user}</td>
                                        <td>{a.title}</td>
                                        <td style={{ fontWeight: 700, color: a.score >= 70 ? '#10b981' : '#f59e0b' }}>
                                            {a.score}/100
                                        </td>
                                        <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                                            {a.date ? new Date(a.date).toLocaleDateString() : '-'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
