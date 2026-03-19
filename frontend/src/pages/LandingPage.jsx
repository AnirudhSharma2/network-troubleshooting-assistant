import { Link } from 'react-router-dom';

const features = [
    {
        icon: (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
        ),
        title: '.pkt File Analysis',
        desc: 'Upload your Packet Tracer .pkt file directly. No CLI copy-paste needed — we parse the XML topology automatically.',
    },
    {
        icon: (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
            </svg>
        ),
        title: '8 Diagnostic Rules',
        desc: 'Deterministic rule engine checks interfaces, routes, VLANs, duplicate IPs, trunk mismatches, and more.',
    },
    {
        icon: (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
        ),
        title: 'Health Scoring',
        desc: 'Get a 0–100 network health score broken down across Routing, Interface, VLAN, and IP categories.',
    },
    {
        icon: (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
            </svg>
        ),
        title: 'PDF Reports',
        desc: 'Export viva-ready PDF reports with all findings, fix commands, and health breakdowns — one click.',
    },
    {
        icon: (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
        ),
        title: 'Learning Mode',
        desc: 'Every detected issue comes with an educational explanation, real-world analogy, and targeted fix command.',
    },
    {
        icon: (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"/>
            </svg>
        ),
        title: 'Practice Scenarios',
        desc: '15+ pre-built labs across 3 difficulty levels — routing, VLAN, interface, IP, and mixed topology scenarios.',
    },
];

const steps = [
    { num: '01', title: 'Upload or Paste', desc: 'Drop your .pkt file or paste Cisco CLI output from Packet Tracer.' },
    { num: '02', title: 'Instant Analysis', desc: 'Our rule engine scans for 20+ failure patterns in under a second.' },
    { num: '03', title: 'Fix & Learn', desc: 'Get exact IOS fix commands and educational explanations for every issue.' },
];

export default function LandingPage() {
    return (
        <div className="landing">
            {/* ── Nav ─────────────────────────────── */}
            <nav className="landing-nav">
                <div className="landing-nav-brand">
                    <div className="landing-logo-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/>
                        </svg>
                    </div>
                    <span className="landing-brand-name">NetAssist</span>
                </div>
                <div className="landing-nav-links">
                    <a href="#features" className="landing-nav-link">Features</a>
                    <a href="#how-it-works" className="landing-nav-link">How it works</a>
                    <Link to="/login" className="landing-nav-link">Sign in</Link>
                    <Link to="/register" className="btn btn-primary btn-sm">Get started free</Link>
                </div>
            </nav>

            {/* ── Hero ────────────────────────────── */}
            <section className="landing-hero">
                <div className="hero-badge">
                    <span className="hero-badge-dot" />
                    Free — No API key required
                </div>
                <h1 className="hero-title">
                    Troubleshoot Cisco Networks<br />
                    <span className="hero-title-accent">in Seconds</span>
                </h1>
                <p className="hero-subtitle">
                    Upload your Packet Tracer <code>.pkt</code> file or paste CLI output. NetAssist
                    diagnoses interface, routing, VLAN, and IP issues instantly — with exact fix commands.
                </p>
                <div className="hero-cta">
                    <Link to="/register" className="btn btn-primary btn-lg">
                        Start troubleshooting free
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
                        </svg>
                    </Link>
                    <Link to="/login" className="btn btn-secondary btn-lg">Sign in</Link>
                </div>
                <div className="hero-stats">
                    <div className="hero-stat">
                        <span className="hero-stat-value">8</span>
                        <span className="hero-stat-label">Diagnostic rules</span>
                    </div>
                    <div className="hero-stat-divider" />
                    <div className="hero-stat">
                        <span className="hero-stat-value">15+</span>
                        <span className="hero-stat-label">Practice labs</span>
                    </div>
                    <div className="hero-stat-divider" />
                    <div className="hero-stat">
                        <span className="hero-stat-value">100%</span>
                        <span className="hero-stat-label">Free forever</span>
                    </div>
                </div>
            </section>

            {/* ── Features ────────────────────────── */}
            <section className="landing-section" id="features">
                <div className="section-label">Features</div>
                <h2 className="section-title">Everything you need to ace your lab</h2>
                <p className="section-subtitle">
                    Built specifically for Cisco Packet Tracer — no real hardware needed.
                </p>
                <div className="features-grid">
                    {features.map((f) => (
                        <div key={f.title} className="feature-card">
                            <div className="feature-icon">{f.icon}</div>
                            <h3 className="feature-title">{f.title}</h3>
                            <p className="feature-desc">{f.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── How it works ────────────────────── */}
            <section className="landing-section landing-section-alt" id="how-it-works">
                <div className="section-label">How it works</div>
                <h2 className="section-title">From broken network to working config</h2>
                <p className="section-subtitle">Three steps — under 30 seconds.</p>
                <div className="steps-grid">
                    {steps.map((s) => (
                        <div key={s.num} className="step-card">
                            <div className="step-num">{s.num}</div>
                            <h3 className="step-title">{s.title}</h3>
                            <p className="step-desc">{s.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── CTA ─────────────────────────────── */}
            <section className="landing-cta-section">
                <div className="landing-cta-card">
                    <h2 className="cta-title">Ready to diagnose your network?</h2>
                    <p className="cta-subtitle">
                        Free forever. No credit card. No AI API key needed.
                    </p>
                    <Link to="/register" className="btn btn-primary btn-lg">
                        Create free account
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
                        </svg>
                    </Link>
                </div>
            </section>

            {/* ── Footer ──────────────────────────── */}
            <footer className="landing-footer">
                <div className="landing-nav-brand">
                    <div className="landing-logo-icon">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/>
                        </svg>
                    </div>
                    <span className="landing-brand-name" style={{ fontSize: 14 }}>NetAssist</span>
                </div>
                <p className="footer-copy">Built for Cisco Packet Tracer labs. Free and open to all students.</p>
            </footer>
        </div>
    );
}
