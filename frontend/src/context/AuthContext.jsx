import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            authAPI.getMe()
                .then((res) => setUser(res.data))
                .catch(() => {
                    localStorage.removeItem('token');
                    setUser(null);
                })
                .finally(() => setLoading(false));
        } else {
            // No token — skip network call, mark auth check as done
            queueMicrotask(() => setLoading(false));
        }
    }, []);

    const login = async (username, password) => {
        const res = await authAPI.login({ username, password });
        localStorage.setItem('token', res.data.access_token);
        setUser(res.data.user);
        return res.data;
    };

    const register = async (data) => {
        const res = await authAPI.register(data);
        localStorage.setItem('token', res.data.access_token);
        setUser(res.data.user);
        return res.data;
    };

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
    };

    const hasRole = (...roles) => {
        return user && roles.includes(user.role);
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, register, logout, hasRole }}>
            {children}
        </AuthContext.Provider>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext);
