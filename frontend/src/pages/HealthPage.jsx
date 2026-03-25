import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { analysisAPI } from '../services/api';

export default function HealthPage() {
    const [searchParams] = useSearchParams();
    const [analyses, setAnalyses] = useState([]);
    const [selected, setSelected] = useState(null);
    const [loading, setLoading] = useState(true);
    const [detailLoading, setDetailLoading] = useState(false);

    const loadDetail = useCallback(async (id) => {
        setDetailLoading(true);
        try {
            const res = await analysisAPI.get(id);
            setSelected(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setDetailLoading(false);
        }
    }, []);

    useEffect(() => {
        analysisAPI.list()
            .then((res) => {
                setAnalyses(res.data);
                const preselect = searchParams.get('id');
                if (preselect) loadDetail(parseInt(preselect));
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [searchParams, loadDetail]);

    const scoreColor = (s) => s >= 70 ? '#10b981' : s >= 40 ? '#f59e0b' : '#ef4444';
    const scoreClass = (s) => s >= 80 ? 'good' : s >= 50 ? 'fair' : 'poor';

    return (
        <div className="fade-in">
            <div className="page-header">
                <h2>Network Health Scoring</h2>
                <p>Detailed breakdown of your network health score with weighted category analysis.</p>
            </div>

            {/* Selector */}
            <div className="card" style={{ marginBottom: 24 }}>
                <div className="card-header"><h3>Select Analysis</h3></div>
                {loading ? (
                    <div className="loading"><div className="spinner"></div></div>
                ) : (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                        {analyses.map((a) => (
                            <button key={a.id} onClick={() => loadDetail(a.id)}
                                className={`btn ${selected?.id === a.id ? 'btn-primary' : 'btn-secondary'}`}>
                                {a.title} — {a.health_score ?? '?'}/100
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {detailLoading && <div className="loading"><div className="spinner"></div></div>}

            {selected && !detailLoading && (
                <div className="fade-in">
                    <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 24 }}>
                        {/* Score Gauge */}
                        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                            <div className="health-gauge">
                                <div className="gauge-circle">
                                    <svg viewBox="0 0 140 140">
                                        <circle className="gauge-bg" cx="70" cy="70" r="62" />
                                        <circle
                                            className="gauge-fill"
                                            cx="70" cy="70" r="62"
                                            stroke={scoreColor(selected.health_score)}
                                            strokeDasharray={2 * Math.PI * 62}
                                            strokeDashoffset={2 * Math.PI * 62 - (selected.health_score / 100) * 2 * Math.PI * 62}
                                        />
                                    </svg>
                                    <div className="gauge-score">
                                        <div className="score-value" style={{ color: scoreColor(selected.health_score) }}>
                                            {Math.round(selected.health_score)}
                                        </div>
                                        <div className="score-label">/ 100</div>
                                    </div>
                                </div>
                            </div>
                            <div style={{ textAlign: 'center', marginTop: 12 }}>
                                <div style={{ fontSize: 18, fontWeight: 700 }}>{selected.title}</div>
                                <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                                    {selected.issues.length} issue(s) detected
                                </div>
                            </div>
                        </div>

                        {/* Category Breakdown */}
                        <div className="card">
                            <div className="card-header"><h3>Category Breakdown</h3></div>
                            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>
                                Score is weighted: Routing 30% · Interface 25% · VLAN 25% · IP 20%
                            </p>

                            {selected.score_breakdown && (
                                <>
                                    {[
                                        { label: 'Routing', key: 'routing_score', weight: '30%' },
                                        { label: 'Interface', key: 'interface_score', weight: '25%' },
                                        { label: 'VLAN', key: 'vlan_score', weight: '25%' },
                                        { label: 'IP', key: 'ip_score', weight: '20%' },
                                    ].map((cat) => {
                                        const val = selected.score_breakdown[cat.key] ?? 100;
                                        return (
                                            <div key={cat.key} className="score-category">
                                                <span className="score-category-label">{cat.label} ({cat.weight})</span>
                                                <div className="score-bar">
                                                    <div
                                                        className={`score-bar-fill ${scoreClass(val)}`}
                                                        style={{ width: `${val}%` }}
                                                    />
                                                </div>
                                                <span className="score-category-value" style={{ color: scoreColor(val) }}>
                                                    {Math.round(val)}%
                                                </span>
                                            </div>
                                        );
                                    })}
                                </>
                            )}

                            {/* Deductions */}
                            {selected.score_breakdown?.deductions?.length > 0 && (
                                <div style={{ marginTop: 24 }}>
                                    <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>📉 Score Deductions</h4>
                                    {selected.score_breakdown.deductions.map((d, i) => (
                                        <div key={i} style={{
                                            display: 'flex', alignItems: 'center', gap: 12,
                                            padding: '8px 12px', marginBottom: 6, fontSize: 13,
                                            background: 'var(--bg-glass)', borderRadius: 'var(--radius-sm)',
                                            borderLeft: `3px solid ${scoreColor(100 - d.deduction * 5)}`
                                        }}>
                                            <span style={{ fontWeight: 700, color: 'var(--color-danger)', minWidth: 40 }}>
                                                -{d.deduction}
                                            </span>
                                            <span style={{ color: 'var(--text-secondary)' }}>{d.reason}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
