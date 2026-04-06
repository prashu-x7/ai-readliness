
import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('ar_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (err) => {
        if (err.response?.status === 401) {

            localStorage.removeItem('ar_token');
            localStorage.removeItem('ar_user');

            if (window.location.pathname !== '/login') {
                window.history.pushState({}, '', '/login');
                window.dispatchEvent(new PopStateEvent('popstate'));
            }
        }
        return Promise.reject(err);
    }
);

export default api;
