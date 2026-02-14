import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE,
    headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Auth
export const authAPI = {
    register: (data) => api.post('/auth/register', data),
    login: (data) => api.post('/auth/login', data),
    getMe: () => api.get('/auth/me'),
};

// Analysis
export const analysisAPI = {
    run: (data) => api.post('/analysis', data),
    list: () => api.get('/analysis'),
    get: (id) => api.get(`/analysis/${id}`),
    getLearning: (id) => api.get(`/analysis/${id}/learning`),
};

// Scenarios
export const scenarioAPI = {
    generate: (data) => api.post('/scenarios/generate', data),
    list: () => api.get('/scenarios'),
    get: (id) => api.get(`/scenarios/${id}`),
};

// Reports
export const reportAPI = {
    downloadPDF: (analysisId) =>
        api.get(`/reports/${analysisId}/pdf`, { responseType: 'blob' }),
};

// Dashboard
export const dashboardAPI = {
    get: () => api.get('/dashboard'),
};

// Admin
export const adminAPI = {
    listUsers: () => api.get('/admin/users'),
    updateRole: (userId, data) => api.put(`/admin/users/${userId}/role`, data),
    deleteUser: (userId) => api.delete(`/admin/users/${userId}`),
    getAnalytics: () => api.get('/admin/analytics'),
};

export default api;
