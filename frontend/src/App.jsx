import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import TroubleshootPage from './pages/TroubleshootPage';
import LearningPage from './pages/LearningPage';
import ScenariosPage from './pages/ScenariosPage';
import HealthPage from './pages/HealthPage';
import ReportsPage from './pages/ReportsPage';
import AdminPage from './pages/AdminPage';
import './index.css';

function ProtectedLayout() {
    const { user, loading } = useAuth();
    if (loading) return <div className="loading"><div className="spinner" /></div>;
    if (!user) return <Navigate to="/" replace />;
    return (
        <div className="app-layout">
            <Sidebar />
            <div className="app-main-wrapper">
                <TopBar />
                <main className="main-content">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}

function AdminRoute() {
    const { hasRole } = useAuth();
    if (!hasRole('admin')) return <Navigate to="/" replace />;
    return <AdminPage />;
}

/** Root: landing for guests, dashboard for authenticated users */
function RootRoute() {
    const { user, loading } = useAuth();
    if (loading) return <div className="loading"><div className="spinner" /></div>;
    if (user) return <Navigate to="/dashboard" replace />;
    return <LandingPage />;
}

/** Public-only routes redirect logged-in users to dashboard */
function PublicRoute({ children }) {
    const { user, loading } = useAuth();
    if (loading) return <div className="loading"><div className="spinner" /></div>;
    if (user) return <Navigate to="/dashboard" replace />;
    return children;
}

function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <Routes>
                    {/* Landing / root */}
                    <Route path="/" element={<RootRoute />} />

                    {/* Public auth routes */}
                    <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
                    <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />

                    {/* Protected app routes */}
                    <Route element={<ProtectedLayout />}>
                        <Route path="/dashboard" element={<DashboardPage />} />
                        <Route path="/troubleshoot" element={<TroubleshootPage />} />
                        <Route path="/learn" element={<LearningPage />} />
                        <Route path="/scenarios" element={<ScenariosPage />} />
                        <Route path="/health" element={<HealthPage />} />
                        <Route path="/reports" element={<ReportsPage />} />
                        <Route path="/admin" element={<AdminRoute />} />
                    </Route>

                    {/* Catch-all */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </AuthProvider>
        </BrowserRouter>
    );
}

export default App;
