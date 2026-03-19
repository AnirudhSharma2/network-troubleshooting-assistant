import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const LogoIcon = () => (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2"/>
        <path d="M8 21h8"/><path d="M12 17v4"/>
    </svg>
);

export default function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await login(username, password);
            navigate('/dashboard');
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed. Please try again.');
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

                <h2>Welcome back</h2>
                <p className="subtitle">Sign in to your account to continue</p>

                {error && <div className="error-message">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Username</label>
                        <input
                            type="text"
                            className="form-input"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter your username"
                            autoComplete="username"
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label>Password</label>
                        <input
                            type="password"
                            className="form-input"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                            autoComplete="current-password"
                            required
                        />
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? 'Signing in...' : 'Sign in'}
                    </button>
                </form>

                <div className="auth-footer">
                    Don't have an account? <Link to="/register">Create one free</Link>
                </div>
                <div className="auth-footer" style={{ marginTop: 8 }}>
                    <Link to="/" style={{ color: 'var(--text-muted)', fontSize: 13 }}>← Back to home</Link>
                </div>
            </div>
        </div>
    );
}
