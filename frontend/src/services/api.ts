import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://researchmate-aznu.onrender.com';

const api = axios.create({
  baseURL: API_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const requestUrl = error.config?.url;
      if (requestUrl && !requestUrl.includes('/api/auth/login')) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export interface User {
  id: string;
  email: string;
  nickname: string;
  created_at: string;
  last_login?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface FinancialReport {
  id: string;
  user_id: string;
  company_name: string;
  stock_code?: string;
  report_period?: string;
  revenue?: number;
  net_profit?: number;
  cash_flow?: number;
  debt_ratio?: number;
  gross_margin?: number;
  ai_summary?: string;
  status: string;
  upload_time: string;
}

export interface Follow {
  id: string;
  user_id: string;
  company_name: string;
  stock_code?: string;
  created_at: string;
}

export interface NewsArticle {
  id: string;
  company_name: string;
  title: string;
  source: string;
  url: string;
  publish_time: string;
  emotion_score?: number;
  emotion_label?: string;
  created_at: string;
}

export interface NewsListResponse {
  total: number;
  items: NewsArticle[];
}

export interface EmotionScore {
  company_name: string;
  current_score: number;
  current_label: string;
  last_7d_avg: number;
  last_30d_avg: number;
}

export interface EmotionTrendData {
  date: string;
  daily_score: number;
  article_count: number;
}

export interface EmotionTrendResponse {
  company_name: string;
  trend: EmotionTrendData[];
}

export const authApi = {
  register: (data: { email: string; password: string; nickname: string }) =>
    api.post<User>('/api/auth/register', data),
  
  login: (data: { email: string; password: string }) =>
    api.post<TokenResponse>('/api/auth/login', data),
  
  getMe: () => api.get<User>('/api/auth/me'),
};

export const reportApi = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<FinancialReport>('/api/reports', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  getAll: () => api.get<FinancialReport[]>('/api/reports'),
  
  getById: (id: string) => api.get<FinancialReport>(`/api/reports/${id}`),
  
  update: (id: string, data: Partial<FinancialReport>) =>
    api.put<FinancialReport>(`/api/reports/${id}`, data),
  
  delete: (id: string) => api.delete(`/api/reports/${id}`),
};

export const newsApi = {
  follow: (data: { company_name: string; stock_code?: string }) =>
    api.post<Follow>('/api/follows', data),
  
  getFollows: () => api.get<Follow[]>('/api/follows'),
  
  unfollow: (id: string) => api.delete(`/api/follows/${id}`),
  
  getNews: (params?: { company_name?: string; limit?: number; offset?: number }) =>
    api.get<NewsListResponse>('/api/news', { params }),
};

export const emotionApi = {
  getScore: (company_name: string) =>
    api.get<EmotionScore>(`/api/emotion/${company_name}`),
  
  getTrend: (company_name: string, days?: number) =>
    api.get<EmotionTrendResponse>(`/api/emotion/${company_name}/trend`, {
      params: { days },
    }),
};

export default api;
