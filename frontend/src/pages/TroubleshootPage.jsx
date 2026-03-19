import { useState, useRef, useCallback } from 'react';
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

function ScoreGauge({ score }) {
    const color = score >= 70 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444';
    const circumference = 2 * Math.PI * 54;
    const offset = circumference - (score / 100) * circumference;
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
            <div style={{ position: 'relative', width: 120, height: 120, flexShrink: 0 }}>
                <svg viewBox="0 0 120 120" width="120" height="120" style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx="60" cy="60" r="54" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
                    <circle
                        cx="60" cy="60" r="54" fill="none"
                        stroke={color} strokeWidth="10" strokeLinecap="round"
                        strokeDasharray={circumference} strokeDashoffset={offset}
                        style={{ transition: 'stroke-dashoffset 1s ease-out' }}
                    />
                </svg>
                <div style={{
                    position: 'absolute', inset: 0, display: 'flex',
                    flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                }}>
                    <span style={{ fontSize: 28, fontWeight: 800, color, lineHeight: 1 }}>{Math.round(score)}</span>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>/ 100</span>
                </div>
            </div>
            <div>
                <div style={{ fontSize: 20, fontWeight: 800, marginBottom: 4 }}>Network Health</div>
                <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
                    {score >= 70 ? 'Good — minor issues detected' : score >= 40 ? 'Fair — attention needed' : 'Critical — immediate action required'}
                </div>
            </div>
        </div>
    );
}

export default function TroubleshootPage() {
    const [tab, setTab] = useState('cli'); // 'cli' | 'pkt'

    // CLI tab state
    const [input, setInput] = useState('');
    const [title, setTitle] = useState('');

    // PKT tab state
    const [pktFile, setPktFile] = useState(null);
    const [pktTitle, setPktTitle] = useState('');
    const [dragging, setDragging] = useState(false);
    const fileInputRef = useRef(null);

    // Shared
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    /* ── CLI handlers ─────────────────────────────────────────── */
    const handleAnalyzeCLI = async () => {
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
            setError(err.response?.data?.detail || 'Analysis failed. Check that the backend is running.');
        } finally {
            setLoading(false);
        }
    };

    /* ── PKT handlers ─────────────────────────────────────────── */
    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setDragging(false);
        const file = e.dataTransfer.files[0];
        if (file && file.name.endsWith('.pkt')) {
            setPktFile(file);
            setPktTitle(file.name.replace('.pkt', '') + ' Analysis');
            setError('');
        } else {
            setError('Please drop a .pkt file.');
        }
    }, []);

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            setPktFile(file);
            setPktTitle(file.name.replace('.pkt', '') + ' Analysis');
            setError('');
        }
    };

    const handleAnalyzePKT = async () => {
        if (!pktFile) {
            setError('Please select a .pkt file first.');
            return;
        }
        setError('');
        setLoading(true);
        setResult(null);
        try {
            const res = await analysisAPI.uploadPkt(pktFile, pktTitle);
            setResult(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to parse .pkt file.');
        } finally {
            setLoading(false);
        }
    };

    const scoreColor = (s) => s >= 70 ? '#10b981' : s >= 40 ? '#f59e0b' : '#ef4444';

    return (
        <div className="fade-in">
            <div className="page-header">
                <h2>Network Troubleshooting</h2>
                <p>Upload a .pkt file or paste Cisco CLI output to diagnose network issues instantly.</p>
            </div>

            {/* Tab switcher */}
            <div className="tab-bar" style={{ marginBottom: 24 }}>
                <button
                    className={`tab-btn${tab === 'cli' ? ' active' : ''}`}
                    onClick={() => { setTab('cli'); setResult(null); setError(''); }}
                >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>
                    </svg>
                    Paste CLI Output
                </button>
                <button
                    className={`tab-btn${tab === 'pkt' ? ' active' : ''}`}
                    onClick={() => { setTab('pkt'); setResult(null); setError(''); }}
                >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                    Upload .pkt File
                </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: result ? '1fr 1fr' : '1fr', gap: 24 }}>

                {/* ── Input Panel ───────────────────────────────── */}
                {tab === 'cli' ? (
                    <div className="card">
                        <div className="card-header">
                            <h3>CLI / Running Config</h3>
                            <button onClick={() => { setInput(SAMPLE_CONFIG); setTitle('Sample Router R1'); }} className="btn btn-sm btn-secondary">
                                Load sample
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
                                placeholder={'Paste your Cisco CLI output here...\n\nSupported:\n• show ip interface brief\n• show ip route\n• show vlan brief\n• show running-config'}
                                style={{ minHeight: 300 }}
                            />
                        </div>
                        {error && <div className="error-message">{error}</div>}
                        <button onClick={handleAnalyzeCLI} className="btn btn-primary" disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
                            {loading ? (
                                <>
                                    <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                                    Analyzing...
                                </>
                            ) : (
                                <>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                                    </svg>
                                    Run Analysis
                                </>
                            )}
                        </button>
                    </div>
                ) : (
                    <div className="card">
                        <div className="card-header">
                            <h3>Packet Tracer File</h3>
                            <span className="badge badge-low">ZIP-XML format</span>
                        </div>

                        {/* Drop zone */}
                        <div
                            className={`pkt-dropzone${dragging ? ' dragging' : ''}${pktFile ? ' has-file' : ''}`}
                            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                            onDragLeave={() => setDragging(false)}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <input
                                type="file"
                                accept=".pkt"
                                ref={fileInputRef}
                                style={{ display: 'none' }}
                                onChange={handleFileSelect}
                            />
                            {pktFile ? (
                                <>
                                    <div className="pkt-file-icon">
                                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                            <polyline points="14 2 14 8 20 8"/>
                                        </svg>
                                    </div>
                                    <div className="pkt-file-name">{pktFile.name}</div>
                                    <div className="pkt-file-size">{(pktFile.size / 1024).toFixed(1)} KB — click to change</div>
                                </>
                            ) : (
                                <>
                                    <div className="pkt-upload-icon">
                                        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                            <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                                        </svg>
                                    </div>
                                    <div className="pkt-upload-text">Drop your .pkt file here</div>
                                    <div className="pkt-upload-sub">or click to browse — Packet Tracer 5.x+ required</div>
                                </>
                            )}
                        </div>

                        <div className="form-group" style={{ marginTop: 16 }}>
                            <label>Analysis Title</label>
                            <input
                                type="text"
                                className="form-input"
                                value={pktTitle}
                                onChange={(e) => setPktTitle(e.target.value)}
                                placeholder="e.g., Lab 3 — OSPF Topology"
                            />
                        </div>

                        <div className="pkt-info-box">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                            </svg>
                            <span>Packet Tracer 5.x+ saves .pkt files as ZIP-compressed XML. Older binary files are not supported — use CLI paste instead.</span>
                        </div>

                        {error && <div className="error-message" style={{ marginTop: 12 }}>{error}</div>}

                        <button onClick={handleAnalyzePKT} className="btn btn-primary" disabled={loading || !pktFile} style={{ width: '100%', justifyContent: 'center', marginTop: 16 }}>
                            {loading ? (
                                <>
                                    <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                                    Parsing .pkt file...
                                </>
                            ) : (
                                <>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                                    </svg>
                                    Analyze .pkt File
                                </>
                            )}
                        </button>
                    </div>
                )}

                {/* ── Results Panel ─────────────────────────────── */}
                {result && (
                    <div className="slide-in">
                        {/* Score */}
                        <div className="card" style={{ marginBottom: 20 }}>
                            <ScoreGauge score={result.health_score} />
                            {result.input_type === 'pkt_file' && (
                                <div className="pkt-source-badge">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                        <polyline points="14 2 14 8 20 8"/>
                                    </svg>
                                    Source: Packet Tracer .pkt file
                                </div>
                            )}
                        </div>

                        {/* Score breakdown */}
                        {result.score_breakdown && (
                            <div className="card" style={{ marginBottom: 20 }}>
                                <div className="card-header"><h3>Score Breakdown</h3></div>
                                {[
                                    { label: 'Routing', key: 'routing_score', weight: '30%' },
                                    { label: 'Interface', key: 'interface_score', weight: '25%' },
                                    { label: 'VLAN', key: 'vlan_score', weight: '25%' },
                                    { label: 'IP', key: 'ip_score', weight: '20%' },
                                ].map(({ label, key, weight }) => {
                                    const val = result.score_breakdown[key] ?? 100;
                                    const cls = val >= 70 ? 'good' : val >= 40 ? 'fair' : 'poor';
                                    return (
                                        <div key={key} className="score-category">
                                            <span className="score-category-label">{label}</span>
                                            <span style={{ fontSize: 11, color: 'var(--text-muted)', marginRight: 8, width: 32 }}>{weight}</span>
                                            <div className="score-bar">
                                                <div className={`score-bar-fill ${cls}`} style={{ width: `${val}%` }} />
                                            </div>
                                            <span className="score-category-value" style={{ color: val >= 70 ? '#10b981' : val >= 40 ? '#f59e0b' : '#ef4444' }}>
                                                {Math.round(val)}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        )}

                        {/* Issues */}
                        <div className="card" style={{ marginBottom: 20 }}>
                            <div className="card-header">
                                <h3>Detected Issues</h3>
                                <span className="badge badge-high">{result.issues.length} found</span>
                            </div>
                            {result.issues.length === 0 ? (
                                <div className="empty-state">
                                    <div className="empty-icon">
                                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--color-success)' }}>
                                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                                            <polyline points="22 4 12 14.01 9 11.01"/>
                                        </svg>
                                    </div>
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
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                                                <circle cx="12" cy="10" r="3"/>
                                            </svg>
                                            {issue.device} — {issue.interface}
                                        </div>
                                        <div className="issue-detail">{issue.detail}</div>
                                        {issue.fix_command && (
                                            <div className="issue-fix">
                                                <div className="issue-fix-label">Recommended Fix</div>
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
                                <div className="card-header"><h3>Analysis Summary</h3></div>
                                <div style={{ whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.8, color: 'var(--text-secondary)' }}>
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
