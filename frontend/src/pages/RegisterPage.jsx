import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const LogoIcon = () => (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2"/>
        <path d="M8 21h8"/><path d="M12 17v4"/>
    </svg>
);

export default function RegisterPage() {
    const [form, setForm] = useState({ username: '', email: '', password: '', full_name: '' });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { register } = useAuth();
    const navigate = useNavigate();

    const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await register(form);
            navigate('/dashboard');
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card fade-in">
                <div style={{ textAlign: 'center', marginBottom: 28 }}>
                    <div style={{
                        width: 60, height: 60, borderRadius: 16,
                        background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                        marginBottom: 16, boxShadow: '0 0 24px rgba(99, 102, 241, 0.35)',
                    }}>
                        <LogoIcon />
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.05em', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
                        NetAssist
                    </div>
                </div>

                <h2>Create your account</h2>
                <p className="subtitle">Free forever — no credit card required</p>

                {error && <div className="error-message">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Full Name</label>
                        <input
                            type="text" name="full_name" className="form-input"
                            value={form.full_name} onChange={handleChange}
                            placeholder="Jane Doe"
                        />
                    </div>
                    <div className="form-group">
                        <label>Username</label>
                        <input
                            type="text" name="username" className="form-input"
                            value={form.username} onChange={handleChange}
                            placeholder="janedoe" required autoComplete="username"
                        />
                    </div>
                    <div className="form-group">
                        <label>Email</label>
                        <input
                            type="email" name="email" className="form-input"
                            value={form.email} onChange={handleChange}
                            placeholder="jane@example.com" required
                        />
                    </div>
                    <div className="form-group">
                        <label>Password</label>
                        <input
                            type="password" name="password" className="form-input"
                            value={form.password} onChange={handleChange}
                            placeholder="Min. 6 characters" required minLength={6}
                            autoComplete="new-password"
                        />
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? 'Creating account...' : 'Create free account'}
                    </button>
                </form>

                <div className="auth-footer">
                    Already have an account? <Link to="/login">Sign in</Link>
                </div>
                <div className="auth-footer" style={{ marginTop: 8 }}>
                    <Link to="/" style={{ color: 'var(--text-muted)', fontSize: 13 }}>← Back to home</Link>
                </div>
            </div>
        </div>
    );
}
