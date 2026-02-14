import { useState, useEffect } from 'react';
import { analysisAPI, reportAPI } from '../services/api';

export default function ReportsPage() {
    const [analyses, setAnalyses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [downloading, setDownloading] = useState(null);

    useEffect(() => {
        analysisAPI.list()
            .then((res) => setAnalyses(res.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const downloadPDF = async (id, title) => {
        setDownloading(id);
        try {
            const res = await reportAPI.downloadPDF(id);
            const blob = new Blob([res.data], { type: 'application/pdf' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `report_${title.replace(/\s+/g, '_')}.pdf`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Download failed', err);
        } finally {
            setDownloading(null);
        }
    };

    const scoreColor = (s) => s >= 70 ? '#10b981' : s >= 40 ? '#f59e0b' : '#ef4444';

    return (
        <div className="fade-in">
            <div className="page-header">
                <h2>Reports</h2>
                <p>Download professional PDF troubleshooting reports for documentation or viva submission.</p>
            </div>

            <div className="card">
                {loading ? (
                    <div className="loading"><div className="spinner"></div></div>
                ) : analyses.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-icon">📄</div>
                        <h3>No Reports Available</h3>
                        <p>Run a troubleshooting analysis first, then come back to download your report.</p>
                    </div>
                ) : (
                    <div className="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Title</th>
                                    <th>Health Score</th>
                                    <th>Issues</th>
                                    <th>Date</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {analyses.map((a) => (
                                    <tr key={a.id}>
                                        <td style={{ fontWeight: 600 }}>{a.title}</td>
                                        <td>
                                            <span style={{ color: scoreColor(a.health_score ?? 0), fontWeight: 700 }}>
                                                {a.health_score ?? 'N/A'}/100
                                            </span>
                                        </td>
                                        <td>{a.issue_count}</td>
                                        <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                                            {a.created_at ? new Date(a.created_at).toLocaleDateString() : '-'}
                                        </td>
                                        <td>
                                            <button
                                                onClick={() => downloadPDF(a.id, a.title)}
                                                className="btn btn-sm btn-primary"
                                                disabled={downloading === a.id}
                                            >
                                                {downloading === a.id ? '⏳' : '📥'} Download PDF
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
