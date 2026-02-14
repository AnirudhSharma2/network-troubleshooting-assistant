import { useState, useEffect } from 'react';
import { scenarioAPI } from '../services/api';

export default function ScenariosPage() {
    const [scenarios, setScenarios] = useState([]);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [form, setForm] = useState({ scenario_type: 'routing', difficulty: 'medium' });
    const [expanded, setExpanded] = useState(null);

    const fetchScenarios = () => {
        scenarioAPI.list()
            .then((res) => setScenarios(res.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    };

    useEffect(() => { fetchScenarios(); }, []);

    const handleGenerate = async () => {
        setGenerating(true);
        try {
            const res = await scenarioAPI.generate(form);
            setScenarios((prev) => [res.data, ...prev]);
            setExpanded(res.data.id);
        } catch (err) {
            console.error(err);
        } finally {
            setGenerating(false);
        }
    };

    return (
        <div className="fade-in">
            <div className="page-header">
                <h2>Scenario Generator</h2>
                <p>Generate broken network scenarios for hands-on practice in Packet Tracer.</p>
            </div>

            {/* Generator Controls */}
            <div className="card" style={{ marginBottom: 24 }}>
                <div className="card-header">
                    <h3>🧪 Generate New Scenario</h3>
                </div>
                <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                    <div className="form-group" style={{ marginBottom: 0, flex: 1, minWidth: 200 }}>
                        <label>Scenario Type</label>
                        <select
                            className="form-input"
                            value={form.scenario_type}
                            onChange={(e) => setForm({ ...form, scenario_type: e.target.value })}
                        >
                            <option value="routing">🛤️ Routing Issues</option>
                            <option value="vlan">🏷️ VLAN Mismatch</option>
                            <option value="interface">🔌 Interface Problems</option>
                            <option value="ip">🔢 IP Misconfiguration</option>
                            <option value="mixed">🔀 Mixed (Multiple Issues)</option>
                        </select>
                    </div>
                    <div className="form-group" style={{ marginBottom: 0, flex: 1, minWidth: 200 }}>
                        <label>Difficulty</label>
                        <select
                            className="form-input"
                            value={form.difficulty}
                            onChange={(e) => setForm({ ...form, difficulty: e.target.value })}
                        >
                            <option value="easy">🟢 Easy</option>
                            <option value="medium">🟡 Medium</option>
                            <option value="hard">🔴 Hard</option>
                        </select>
                    </div>
                    <button
                        onClick={handleGenerate}
                        className="btn btn-primary"
                        disabled={generating}
                        style={{ height: 42 }}
                    >
                        {generating ? '⏳ Generating...' : '✨ Generate Scenario'}
                    </button>
                </div>
            </div>

            {/* Scenario List */}
            {loading ? (
                <div className="loading"><div className="spinner"></div></div>
            ) : scenarios.length === 0 ? (
                <div className="card">
                    <div className="empty-state">
                        <div className="empty-icon">🧪</div>
                        <h3>No Scenarios Yet</h3>
                        <p>Generate your first practice scenario above!</p>
                    </div>
                </div>
            ) : (
                <div className="card-grid" style={{ gridTemplateColumns: '1fr' }}>
                    {scenarios.map((s) => (
                        <div key={s.id} className="scenario-card" onClick={() => setExpanded(expanded === s.id ? null : s.id)}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                                <div>
                                    <span className={`scenario-type-badge ${s.scenario_type}`}>{s.scenario_type}</span>
                                    <span className={`scenario-type-badge`} style={{ marginLeft: 8, background: 'var(--bg-glass)', color: 'var(--text-secondary)' }}>
                                        {s.difficulty}
                                    </span>
                                </div>
                                <span style={{ fontSize: 20, cursor: 'pointer' }}>{expanded === s.id ? '🔽' : '▶️'}</span>
                            </div>
                            <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>{s.title}</h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.6 }}>{s.description}</p>

                            {expanded === s.id && (
                                <div className="fade-in" style={{ marginTop: 20 }}>
                                    {s.network_config && (
                                        <div style={{ marginBottom: 16 }}>
                                            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent-primary)', marginBottom: 8 }}>
                                                📋 Network Configuration (intentionally broken)
                                            </div>
                                            <div className="code-block">{s.network_config}</div>
                                        </div>
                                    )}
                                    {s.instructions && (
                                        <div style={{ marginBottom: 16 }}>
                                            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-success)', marginBottom: 8 }}>
                                                📝 Lab Instructions
                                            </div>
                                            <div style={{ whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.7, color: 'var(--text-secondary)' }}>
                                                {s.instructions}
                                            </div>
                                        </div>
                                    )}
                                    {s.expected_issues && s.expected_issues.length > 0 && (
                                        <div>
                                            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-warning)', marginBottom: 8 }}>
                                                🎯 Expected Issues (spoiler!)
                                            </div>
                                            {s.expected_issues.map((issue, j) => (
                                                <div key={j} style={{
                                                    background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.2)',
                                                    borderRadius: 'var(--radius-sm)', padding: '8px 14px', marginBottom: 8, fontSize: 13
                                                }}>
                                                    <strong>{issue.type}:</strong> {issue.detail}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
