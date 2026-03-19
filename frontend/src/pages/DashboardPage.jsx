import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { dashboardAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function DashboardPage() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const { user } = useAuth();

    useEffect(() => {
        dashboardAPI.get()
            .then((res) => setData(res.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading"><div className="spinner"></div></div>;

    const score = data?.average_health_score ?? 100;
    const circumference = 2 * Math.PI * 62;
    const offset = circumference - (score / 100) * circumference;
    const scoreColor = score >= 70 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444';

    return (
        <div className="fade-in">
            <div className="page-header">
                <h2>Welcome back, {user?.full_name || user?.username}</h2>
                <p>Here's your network troubleshooting overview.</p>
            </div>

            {/* Stats Row */}
            <div className="card-grid">
                <div className="stat-card">
                    <div className="stat-icon primary">📊</div>
                    <div>
                        <div className="stat-value">{data?.total_analyses || 0}</div>
                        <div className="stat-label">Total Analyses</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon success">💚</div>
                    <div>
                        <div className="stat-value" style={{ color: scoreColor }}>{score}</div>
                        <div className="stat-label">Avg Health Score</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon warning">⚠️</div>
                    <div>
                        <div className="stat-value">
                            {Object.values(data?.error_summary || {}).reduce((a, b) => a + b, 0)}
                        </div>
                        <div className="stat-label">Total Issues Found</div>
                    </div>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                {/* Health Gauge */}
                <div className="card">
                    <div className="card-header">
                        <h3>Network Health</h3>
                    </div>
                    <div className="health-gauge">
                        <div className="gauge-circle">
                            <svg viewBox="0 0 140 140">
                                <circle className="gauge-bg" cx="70" cy="70" r="62" />
                                <circle
                                    className="gauge-fill"
                                    cx="70" cy="70" r="62"
                                    stroke={scoreColor}
                                    strokeDasharray={circumference}
                                    strokeDashoffset={offset}
                                />
                            </svg>
                            <div className="gauge-score">
                                <div className="score-value" style={{ color: scoreColor }}>{Math.round(score)}</div>
                                <div className="score-label">Health</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="card">
                    <div className="card-header">
                        <h3>Quick Actions</h3>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        <Link to="/troubleshoot" className="btn btn-primary" style={{ justifyContent: 'center' }}>
                            🔍 Run New Analysis
                        </Link>
                        <Link to="/scenarios" className="btn btn-secondary" style={{ justifyContent: 'center' }}>
                            🧪 Generate Scenario
                        </Link>
                        <Link to="/learn" className="btn btn-secondary" style={{ justifyContent: 'center' }}>
                            📚 Learning Mode
                        </Link>
                        <Link to="/reports" className="btn btn-secondary" style={{ justifyContent: 'center' }}>
                            📄 View Reports
                        </Link>
                    </div>
                </div>
            </div>

            {/* Recent Analyses */}
            <div className="card" style={{ marginTop: 20 }}>
                <div className="card-header">
                    <h3>Recent Analyses</h3>
                    <Link to="/troubleshoot" className="btn btn-sm btn-secondary">View All</Link>
                </div>
                {data?.recent_analyses?.length > 0 ? (
                    <div className="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Title</th>
                                    <th>Health Score</th>
                                    <th>Issues</th>
                                    <th>Status</th>
                                    <th>Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.recent_analyses.map((a) => (
                                    <tr key={a.id}>
                                        <td><Link to={`/health?id=${a.id}`} style={{ color: 'var(--accent-primary)', textDecoration: 'none' }}>{a.title}</Link></td>
                                        <td>
                                            <span style={{
                                                color: (a.health_score ?? 100) >= 70 ? '#10b981' : (a.health_score ?? 100) >= 40 ? '#f59e0b' : '#ef4444',
                                                fontWeight: 700
                                            }}>
                                                {a.health_score ?? 'N/A'}/100
                                            </span>
                                        </td>
                                        <td>{a.issue_count}</td>
                                        <td><span className="badge badge-low">{a.status}</span></td>
                                        <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                                            {a.created_at ? new Date(a.created_at).toLocaleDateString() : '-'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="empty-state">
                        <div className="empty-icon">📊</div>
                        <h3>No analyses yet</h3>
                        <p>Run your first troubleshooting analysis to see results here.</p>
                    </div>
                )}
            </div>

            {/* Error Summary */}
            {data?.error_summary && Object.keys(data.error_summary).length > 0 && (
                <div className="card" style={{ marginTop: 20 }}>
                    <div className="card-header">
                        <h3>Error Summary</h3>
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                        {Object.entries(data.error_summary).map(([type, count]) => (
                            <div key={type} style={{
                                background: 'var(--bg-glass)', border: '1px solid var(--border-default)',
                                borderRadius: 'var(--radius-sm)', padding: '10px 16px',
                                display: 'flex', alignItems: 'center', gap: 10
                            }}>
                                <span style={{ fontSize: 20, fontWeight: 800, color: 'var(--color-warning)' }}>{count}</span>
                                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                                    {type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
