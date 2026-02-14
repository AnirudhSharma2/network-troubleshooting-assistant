import { useState } from 'react';
import { analysisAPI } from '../services/api';

const SAMPLE_CONFIG = `hostname R1
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 shutdown
!
interface GigabitEthernet0/1
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
interface Serial0/0/0
 ip address 172.16.0.1 255.255.255.252
 no shutdown
!
router ospf 1
 network 10.0.0.0 0.0.0.255 area 0
!
! Note: Gig0/0 is shutdown and 192.168.1.0 not in OSPF
`;

export default function TroubleshootPage() {
    const [input, setInput] = useState('');
    const [title, setTitle] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleAnalyze = async () => {
        if (input.trim().length < 10) {
            setError('Please paste at least 10 characters of CLI output or config.');
            return;
        }
        setError('');
        setLoading(true);
        setResult(null);
        try {
            const res = await analysisAPI.run({
                title: title || 'Analysis ' + new Date().toLocaleString(),
                input_text: input,
                input_type: 'cli_output',
            });
            setResult(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Analysis failed.');
        } finally {
            setLoading(false);
        }
    };

    const loadSample = () => {
        setInput(SAMPLE_CONFIG);
        setTitle('Sample Router R1 Analysis');
    };

    const scoreColor = (s) => s >= 70 ? '#10b981' : s >= 40 ? '#f59e0b' : '#ef4444';

    return (
        <div className="fade-in">
            <div className="page-header">
                <h2>Network Troubleshooting</h2>
                <p>Paste Cisco CLI output or running-config to diagnose network issues.</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: result ? '1fr 1fr' : '1fr', gap: 24 }}>
                {/* Input Panel */}
                <div className="card">
                    <div className="card-header">
                        <h3>📋 Configuration Input</h3>
                        <button onClick={loadSample} className="btn btn-sm btn-secondary">
                            Load Sample Config
                        </button>
                    </div>

                    <div className="form-group">
                        <label>Analysis Title</label>
                        <input
                            type="text"
                            className="form-input"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="e.g., Router R1 Analysis"
                        />
                    </div>

                    <div className="form-group">
                        <label>CLI Output / Running Config</label>
                        <textarea
                            className="form-input"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={'Paste your Cisco CLI output here...\n\nSupported:\n• show ip interface brief\n• show ip route\n• show vlan brief\n• show running-config\n• Or a combination of the above'}
                            style={{ minHeight: 300 }}
                        />
                    </div>

                    {error && <div className="error-message">{error}</div>}

                    <button
                        onClick={handleAnalyze}
                        className="btn btn-primary"
                        disabled={loading}
                        style={{ width: '100%', justifyContent: 'center' }}
                    >
                        {loading ? '⏳ Analyzing...' : '🔍 Run Analysis'}
                    </button>
                </div>

                {/* Results Panel */}
                {result && (
                    <div className="slide-in">
                        {/* Score Card */}
                        <div className="card" style={{ marginBottom: 20 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
                                <div style={{
                                    width: 80, height: 80, borderRadius: '50%',
                                    background: `conic-gradient(${scoreColor(result.health_score)} ${result.health_score * 3.6}deg, rgba(255,255,255,0.05) 0deg)`,
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                }}>
                                    <div style={{
                                        width: 64, height: 64, borderRadius: '50%', background: 'var(--bg-secondary)',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        fontWeight: 800, fontSize: 22, color: scoreColor(result.health_score)
                                    }}>
                                        {Math.round(result.health_score)}
                                    </div>
                                </div>
                                <div>
                                    <div style={{ fontSize: 20, fontWeight: 800 }}>Health Score</div>
                                    <div style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
                                        {result.issues.length} issue(s) detected
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Issues */}
                        <div className="card" style={{ marginBottom: 20 }}>
                            <div className="card-header">
                                <h3>⚠️ Detected Issues</h3>
                            </div>
                            {result.issues.length === 0 ? (
                                <div className="empty-state">
                                    <div className="empty-icon">✅</div>
                                    <h3>No Issues Detected</h3>
                                    <p>Your network configuration looks clean!</p>
                                </div>
                            ) : (
                                result.issues.map((issue, i) => (
                                    <div key={i} className={`issue-card ${issue.severity}`}>
                                        <div className="issue-header">
                                            <span className="issue-title">
                                                {issue.failure_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                                            </span>
                                            <span className={`badge badge-${issue.severity}`}>{issue.severity}</span>
                                        </div>
                                        <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 8 }}>
                                            📍 {issue.device} → {issue.interface}
                                        </div>
                                        <div className="issue-detail">{issue.detail}</div>
                                        {issue.fix_command && (
                                            <div className="issue-fix">
                                                <div className="issue-fix-label">💡 Recommended Fix</div>
                                                <div className="code-block">{issue.fix_command}</div>
                                            </div>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>

                        {/* Explanation */}
                        {result.explanation && (
                            <div className="card">
                                <div className="card-header">
                                    <h3>📝 Analysis Summary</h3>
                                </div>
                                <div style={{ whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.7, color: 'var(--text-secondary)' }}>
                                    {result.explanation}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
