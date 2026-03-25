import { useState } from 'react';
import { analysisAPI } from '../services/api';

const SAMPLE_CAPTURE = `hostname R1
!
interface GigabitEthernet0/0
 ip address 192.168.10.1 255.255.255.0
 shutdown
!
R1#show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     192.168.10.1    YES manual administratively down down
GigabitEthernet0/1     10.0.0.1        YES manual up                    up
!
R1#show ip route
Gateway of last resort is not set

C    10.0.0.0/24 is directly connected, GigabitEthernet0/1

---
hostname SW1
!
interface FastEthernet0/1
 switchport mode access
 switchport access vlan 99
!
SW1#show vlan brief
VLAN Name                             Status    Ports
1    default                          active    Fa0/2, Fa0/3
10   Sales                            active    Fa0/4
`;

const CLI_STEPS = [
    'Open each Packet Tracer device and capture the relevant CLI output.',
    'Paste multiple devices in one block. Separate them with `---` or include each hostname/prompt.',
    'Run analysis to get evidence coverage, confidence, and a fix order.',
];

const CLI_COMMANDS = [
    { cmd: 'show running-config', desc: 'Configuration context for interfaces, VLANs, and routing protocols' },
    { cmd: 'show ip interface brief', desc: 'Live interface state, IP assignment, and protocol status' },
    { cmd: 'show ip route', desc: 'Routing table, default route, and reachability evidence' },
    { cmd: 'show vlan brief', desc: 'Switch VLAN inventory and access-port assignments' },
];

function CopyButton({ text }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
        } catch {
            setCopied(false);
        }
    };

    return (
        <button
            type="button"
            onClick={handleCopy}
            className="btn btn-sm btn-secondary"
            style={{ padding: '4px 10px', fontSize: 11 }}
        >
            {copied ? 'Copied' : 'Copy'}
        </button>
    );
}

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
                        cx="60"
                        cy="60"
                        r="54"
                        fill="none"
                        stroke={color}
                        strokeWidth="10"
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        style={{ transition: 'stroke-dashoffset 1s ease-out' }}
                    />
                </svg>
                <div
                    style={{
                        position: 'absolute',
                        inset: 0,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                    }}
                >
                    <span style={{ fontSize: 28, fontWeight: 800, color, lineHeight: 1 }}>{Math.round(score)}</span>
                    <span
                        style={{
                            fontSize: 11,
                            color: 'var(--text-muted)',
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em',
                        }}
                    >
                        / 100
                    </span>
                </div>
            </div>
            <div>
                <div style={{ fontSize: 20, fontWeight: 800, marginBottom: 4 }}>Network Health</div>
                <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
                    {score >= 70 ? 'Good baseline' : score >= 40 ? 'Needs attention' : 'Critical path broken'}
                </div>
            </div>
        </div>
    );
}

function MetricCard({ label, value, detail }) {
    return (
        <div
            style={{
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: 16,
            }}
        >
            <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
                {label}
            </div>
            <div style={{ fontSize: 28, fontWeight: 800, marginBottom: 6 }}>{value}</div>
            {detail && <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{detail}</div>}
        </div>
    );
}

function EvidenceBar({ score, confidence }) {
    const color = score >= 80 ? '#10b981' : score >= 55 ? '#f59e0b' : '#ef4444';
    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Capture quality</span>
                <span style={{ fontSize: 13, color, fontWeight: 700 }}>{Math.round(score)}% · {confidence}</span>
            </div>
            <div style={{ height: 10, borderRadius: 999, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                <div style={{ width: `${score}%`, height: '100%', background: color, transition: 'width 0.4s ease' }} />
            </div>
        </div>
    );
}

export default function TroubleshootPage() {
    const [input, setInput] = useState('');
    const [title, setTitle] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleAnalyze = async () => {
        if (input.trim().length < 10) {
            setError('Please paste CLI output or running-config text before analyzing.');
            return;
        }

        setError('');
        setLoading(true);
        setResult(null);

        try {
            const res = await analysisAPI.run({
                title: title || `Capture ${new Date().toLocaleString()}`,
                input_text: input,
                input_type: 'multi_device_cli',
            });
            setResult(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Analysis failed. Check that the backend is running.');
        } finally {
            setLoading(false);
        }
    };

    const parsedSummary = result?.parsed_summary;
    const evidence = result?.evidence;
    const fixPlan = result?.fix_plan || [];
    const insights = result?.insights || [];

    return (
        <div className="fade-in">
            <div className="page-header">
                <h2>Troubleshooting Copilot</h2>
                <p>
                    Deterministic Packet Tracer analysis from pasted CLI captures. This view shows scope,
                    evidence confidence, issue detection, and the best repair order.
                </p>
            </div>

            <div className="card" style={{ marginBottom: 24 }}>
                <div className="card-header">
                    <h3>Packet Tracer Capture Workflow</h3>
                    <span className="badge badge-low">Offline and free</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 20 }}>
                    <div>
                        <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
                            How To Capture
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            {CLI_STEPS.map((step, index) => (
                                <div key={step} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                                    <div
                                        style={{
                                            width: 24,
                                            height: 24,
                                            borderRadius: '50%',
                                            background: 'var(--accent-gradient)',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            fontSize: 12,
                                            fontWeight: 700,
                                            color: 'white',
                                            flexShrink: 0,
                                            marginTop: 1,
                                        }}
                                    >
                                        {index + 1}
                                    </div>
                                    <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{step}</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div>
                        <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
                            Commands To Run
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {CLI_COMMANDS.map(({ cmd, desc }) => (
                                <div
                                    key={cmd}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'space-between',
                                        gap: 12,
                                        padding: '8px 12px',
                                        background: 'rgba(0,0,0,0.25)',
                                        border: '1px solid var(--border-default)',
                                        borderRadius: 'var(--radius-sm)',
                                    }}
                                >
                                    <div>
                                        <code style={{ fontSize: 13, color: 'var(--color-success)', marginRight: 10 }}>{cmd}</code>
                                        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{desc}</span>
                                    </div>
                                    <CopyButton text={cmd} />
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: result ? 'minmax(320px, 1fr) minmax(360px, 1.1fr)' : '1fr', gap: 24 }}>
                <div className="card">
                    <div className="card-header">
                        <h3>Paste CLI Capture</h3>
                        <button
                            type="button"
                            onClick={() => {
                                setInput(SAMPLE_CAPTURE);
                                setTitle('Sample multi-device lab');
                            }}
                            className="btn btn-sm btn-secondary"
                        >
                            Load sample lab
                        </button>
                    </div>

                    <div className="form-group">
                        <label>Capture Title</label>
                        <input
                            type="text"
                            className="form-input"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="e.g., Campus lab attempt 1"
                        />
                    </div>

                    <div className="form-group">
                        <label>CLI Output / Running Config</label>
                        <textarea
                            className="form-input"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={`Paste one or more device captures here...

hostname R1
...
R1#show ip route
...
---
hostname SW1
...
SW1#show vlan brief`}
                            style={{ minHeight: 360 }}
                        />
                    </div>

                    <div
                        style={{
                            background: 'rgba(59, 130, 246, 0.06)',
                            border: '1px solid rgba(59, 130, 246, 0.2)',
                            borderRadius: 'var(--radius-sm)',
                            padding: '12px 14px',
                            fontSize: 13,
                            color: 'var(--text-secondary)',
                            lineHeight: 1.6,
                            marginBottom: 16,
                        }}
                    >
                        This project now avoids fake `.pkt` parsing claims. It works from real CLI evidence and can
                        process combined multi-device captures in one analysis.
                    </div>

                    {error && <div className="error-message">{error}</div>}

                    <button
                        type="button"
                        onClick={handleAnalyze}
                        className="btn btn-primary"
                        disabled={loading}
                        style={{ width: '100%', justifyContent: 'center' }}
                    >
                        {loading ? (
                            <>
                                <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                                Analyzing capture...
                            </>
                        ) : (
                            <>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <circle cx="11" cy="11" r="8" />
                                    <path d="m21 21-4.35-4.35" />
                                </svg>
                                Run deterministic analysis
                            </>
                        )}
                    </button>
                </div>

                {result && (
                    <div className="slide-in">
                        <div className="card" style={{ marginBottom: 20 }}>
                            <div className="card-header">
                                <h3>Analysis Overview</h3>
                                <span className="badge badge-low">{result.engine_mode?.replace(/_/g, ' ') || 'deterministic copilot'}</span>
                            </div>
                            <ScoreGauge score={result.health_score} />

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginTop: 18 }}>
                                <MetricCard
                                    label="Devices"
                                    value={parsedSummary?.device_count ?? 1}
                                    detail={parsedSummary?.device_names?.join(', ') || 'Single capture'}
                                />
                                <MetricCard
                                    label="Issues"
                                    value={result.issues.length}
                                    detail="Rule violations detected in this capture"
                                />
                                <MetricCard
                                    label="Confidence"
                                    value={`${Math.round(evidence?.overall_score ?? 0)}%`}
                                    detail={evidence?.summary || 'No evidence summary available'}
                                />
                            </div>
                        </div>

                        {insights.length > 0 && (
                            <div className="card" style={{ marginBottom: 20 }}>
                                <div className="card-header"><h3>Key Insights</h3></div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                    {insights.map((insight) => (
                                        <div
                                            key={insight}
                                            style={{
                                                padding: '12px 14px',
                                                borderRadius: 'var(--radius-sm)',
                                                border: '1px solid var(--border-default)',
                                                background: 'rgba(255,255,255,0.03)',
                                                color: 'var(--text-secondary)',
                                                lineHeight: 1.5,
                                            }}
                                        >
                                            {insight}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {evidence && (
                            <div className="card" style={{ marginBottom: 20 }}>
                                <div className="card-header">
                                    <h3>Evidence Coverage</h3>
                                    <span className={`badge badge-${evidence.confidence === 'high' ? 'low' : evidence.confidence === 'medium' ? 'medium' : 'high'}`}>
                                        {evidence.confidence} confidence
                                    </span>
                                </div>

                                <EvidenceBar score={evidence.overall_score} confidence={evidence.confidence} />

                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10, marginTop: 16 }}>
                                    {evidence.command_checks.map((check) => (
                                        <div
                                            key={check.key}
                                            style={{
                                                border: `1px solid ${check.detected ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-default)'}`,
                                                background: check.detected ? 'rgba(16, 185, 129, 0.06)' : 'rgba(255,255,255,0.03)',
                                                borderRadius: 'var(--radius-sm)',
                                                padding: 12,
                                            }}
                                        >
                                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginBottom: 8 }}>
                                                <strong style={{ fontSize: 13 }}>{check.label}</strong>
                                                <span style={{ color: check.detected ? '#10b981' : 'var(--text-muted)', fontSize: 12 }}>
                                                    {check.detected ? 'Detected' : 'Missing'}
                                                </span>
                                            </div>
                                            <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{check.why}</div>
                                        </div>
                                    ))}
                                </div>

                                {evidence.missing_commands.length > 0 && (
                                    <div style={{ marginTop: 18 }}>
                                        <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 10 }}>
                                            Next Commands To Capture
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                            {evidence.missing_commands.map((item) => (
                                                <div
                                                    key={`${item.command}-${item.reason}`}
                                                    style={{
                                                        display: 'flex',
                                                        justifyContent: 'space-between',
                                                        gap: 12,
                                                        alignItems: 'flex-start',
                                                        border: '1px solid var(--border-default)',
                                                        borderRadius: 'var(--radius-sm)',
                                                        padding: '10px 12px',
                                                        background: 'rgba(255,255,255,0.02)',
                                                    }}
                                                >
                                                    <div>
                                                        <code style={{ fontSize: 13, color: 'var(--color-warning)' }}>{item.command}</code>
                                                        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.5 }}>
                                                            {item.reason}
                                                        </div>
                                                    </div>
                                                    <CopyButton text={item.command} />
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {evidence.notes?.length > 0 && (
                                    <div style={{ marginTop: 18, display: 'flex', flexDirection: 'column', gap: 8 }}>
                                        {evidence.notes.map((note) => (
                                            <div
                                                key={note}
                                                style={{
                                                    padding: '10px 12px',
                                                    borderRadius: 'var(--radius-sm)',
                                                    background: 'rgba(245, 158, 11, 0.06)',
                                                    border: '1px solid rgba(245, 158, 11, 0.2)',
                                                    color: 'var(--text-secondary)',
                                                    fontSize: 13,
                                                }}
                                            >
                                                {note}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        {fixPlan.length > 0 && (
                            <div className="card" style={{ marginBottom: 20 }}>
                                <div className="card-header">
                                    <h3>Priority Fix Plan</h3>
                                    <span className="badge badge-high">{fixPlan.length} steps</span>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                    {fixPlan.map((step) => (
                                        <div
                                            key={`${step.priority}-${step.failure_type}`}
                                            style={{
                                                border: '1px solid var(--border-default)',
                                                borderRadius: 'var(--radius-md)',
                                                padding: 14,
                                                background: 'rgba(255,255,255,0.03)',
                                            }}
                                        >
                                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 10 }}>
                                                <div>
                                                    <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                                                        Priority {step.priority}
                                                    </div>
                                                    <div style={{ fontSize: 18, fontWeight: 800 }}>{step.title}</div>
                                                </div>
                                                <span className={`badge badge-${step.severity}`}>{step.severity}</span>
                                            </div>

                                            <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 10 }}>
                                                {step.summary}
                                            </div>

                                            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>
                                                {step.issue_count} issue(s) · Devices: {step.devices.join(', ')}
                                            </div>

                                            {step.commands.length > 0 && (
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                    {step.commands.slice(0, 2).map((command) => (
                                                        <div key={command} style={{ display: 'flex', gap: 12, justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                                            <div className="code-block" style={{ flex: 1, marginBottom: 0 }}>{command}</div>
                                                            <CopyButton text={command} />
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

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
                                            <span
                                                className="score-category-value"
                                                style={{ color: val >= 70 ? '#10b981' : val >= 40 ? '#f59e0b' : '#ef4444' }}
                                            >
                                                {Math.round(val)}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        )}

                        <div className="card" style={{ marginBottom: 20 }}>
                            <div className="card-header">
                                <h3>Detected Issues</h3>
                                <span className="badge badge-high">{result.issues.length} found</span>
                            </div>
                            {result.issues.length === 0 ? (
                                <div className="empty-state">
                                    <div className="empty-icon">
                                        <svg
                                            width="48"
                                            height="48"
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            stroke="currentColor"
                                            strokeWidth="1.5"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            style={{ color: 'var(--color-success)' }}
                                        >
                                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                                            <polyline points="22 4 12 14.01 9 11.01" />
                                        </svg>
                                    </div>
                                    <h3>No Issues Detected</h3>
                                    <p>No rule violations were found in the captured evidence.</p>
                                </div>
                            ) : (
                                result.issues.map((issue, index) => (
                                    <div key={`${issue.failure_type}-${index}`} className={`issue-card ${issue.severity}`}>
                                        <div className="issue-header">
                                            <span className="issue-title">
                                                {issue.failure_type.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())}
                                            </span>
                                            <span className={`badge badge-${issue.severity}`}>{issue.severity}</span>
                                        </div>
                                        <div
                                            style={{
                                                fontSize: 12,
                                                color: 'var(--text-muted)',
                                                marginBottom: 8,
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: 6,
                                            }}
                                        >
                                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                                                <circle cx="12" cy="10" r="3" />
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

                        <div className="card">
                            <div className="card-header"><h3>Operational Brief</h3></div>
                            <div style={{ whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.8, color: 'var(--text-secondary)' }}>
                                {result.explanation}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
