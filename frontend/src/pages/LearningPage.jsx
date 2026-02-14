import { useState, useEffect } from 'react';
import { analysisAPI } from '../services/api';

export default function LearningPage() {
    const [analyses, setAnalyses] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [content, setContent] = useState(null);
    const [loading, setLoading] = useState(false);
    const [listLoading, setListLoading] = useState(true);

    useEffect(() => {
        analysisAPI.list()
            .then((res) => setAnalyses(res.data))
            .catch(console.error)
            .finally(() => setListLoading(false));
    }, []);

    const loadLearning = async (id) => {
        setSelectedId(id);
        setLoading(true);
        try {
            const res = await analysisAPI.getLearning(id);
            setContent(res.data.learning_content);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fade-in">
            <div className="page-header">
                <h2>Learning Mode</h2>
                <p>Understand WHY network issues happen and HOW fixes work. Select an analysis to learn from it.</p>
            </div>

            {/* Analysis Selector */}
            <div className="card" style={{ marginBottom: 24 }}>
                <div className="card-header">
                    <h3>📚 Select an Analysis to Study</h3>
                </div>
                {listLoading ? (
                    <div className="loading"><div className="spinner"></div></div>
                ) : analyses.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-icon">📋</div>
                        <h3>No analyses available</h3>
                        <p>Run a troubleshooting analysis first, then come back to learn from it.</p>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                        {analyses.map((a) => (
                            <button
                                key={a.id}
                                onClick={() => loadLearning(a.id)}
                                className={`btn ${selectedId === a.id ? 'btn-primary' : 'btn-secondary'}`}
                            >
                                {a.title} ({a.issue_count} issues)
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Learning Content */}
            {loading && <div className="loading"><div className="spinner"></div></div>}

            {content && !loading && (
                <div className="fade-in">
                    {content.length === 0 ? (
                        <div className="card">
                            <div className="empty-state">
                                <div className="empty-icon">✅</div>
                                <h3>Perfect Score!</h3>
                                <p>This analysis had no issues — nothing to learn from here. Try an analysis with detected problems.</p>
                            </div>
                        </div>
                    ) : (
                        content.map((item, i) => (
                            <div key={i} className="learning-card slide-in" style={{ animationDelay: `${i * 0.1}s` }}>
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                                    <h4>📖 {item.concept}</h4>
                                    <span className={`badge badge-${item.severity}`}>{item.severity}</span>
                                </div>

                                <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
                                    📍 {item.device} → {item.interface}
                                </div>

                                <div className="learning-section">
                                    <div className="learning-section-label">What happened?</div>
                                    <p>{item.explanation}</p>
                                </div>

                                <div className="learning-section">
                                    <div className="learning-section-label">Why does the fix work?</div>
                                    <p>{item.why_fix_works}</p>
                                </div>

                                {item.fix_command && (
                                    <div className="learning-section">
                                        <div className="learning-section-label">Fix Command</div>
                                        <div className="code-block">{item.fix_command}</div>
                                    </div>
                                )}

                                <div className="learning-section">
                                    <div className="learning-section-label">💡 Real-World Analogy</div>
                                    <div className="analogy-box">{item.analogy}</div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
}
