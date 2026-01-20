import axios from 'axios';
import Cookies from 'js-cookie';

// Dynamic API URL selection
const API_URL = typeof window !== 'undefined'
    ? `http://${window.location.hostname}:8000`
    : 'http://localhost:8000';

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add token
api.interceptors.request.use((config) => {
    const token = Cookies.get('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response interceptor to log errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('API Error:', {
            url: error.config?.url,
            method: error.config?.method,
            status: error.response?.status,
            data: error.response?.data,
            message: error.message
        });
        return Promise.reject(error);
    }
);

export interface User {
    id: number;
    username: string;
    full_name: string;
    role: string;
}

export const login = async (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });

    const { access_token, user_id, role, full_name } = response.data;
    Cookies.set('token', access_token, { expires: 7 }); // 7 days
    Cookies.set('user', JSON.stringify({ id: user_id, username, role, full_name }), { expires: 7 });

    return response.data;
};

export const joinMeeting = async (id: string) => {
    const response = await api.post(`/meetings/${id}/join`);
    return response.data;
};

export const logout = () => {
    Cookies.remove('token');
    Cookies.remove('user');
    window.location.href = '/login';
};

export const getCurrentUser = (): User | null => {
    const userStr = Cookies.get('user');
    return userStr ? JSON.parse(userStr) : null;
};

export interface Task {
    id: number;
    title: string;
    status: 'pending' | 'in_progress' | 'review' | 'completed';
    priority?: string;
    assignee?: string;
    description?: string;
}

export interface Meeting {
    id: number;
    title: string;
    date: string;
    status: 'recorded' | 'queued' | 'processing' | 'completed' | 'scheduled';
}

export interface MeetingDetail extends Meeting {
    transcript?: string;
    summary?: string;
    audio_url?: string;
    tasks: Task[];
}

export const fetchMeetings = async (): Promise<Meeting[]> => {
    const response = await api.get('/meetings');
    return response.data;
};

export const fetchMeeting = async (id: number): Promise<MeetingDetail> => {
    const response = await api.get(`/meetings/${id}`);
    return response.data;
};

export const uploadMeeting = async (file: File, title: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);

    const response = await api.post('/upload_audio', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const processMeeting = async (filename: string, title: string, meetingId?: number) => {
    const response = await api.post('/process_meeting', { filename, title, meeting_id: meetingId });
    return response.data;
};

export const uploadMeetingAudio = async (blob: Blob, meetingId: string, title: string) => {
    const formData = new FormData();
    const filename = `meeting_${meetingId}_${Date.now()}.wav`;
    formData.append('file', blob, filename);
    formData.append('title', title);

    const response = await api.post('/upload_audio', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });

    // Now trigger processing for the existing meeting
    if (response.data.info) {
        await processMeeting(`data/${filename}`, title, parseInt(meetingId));
    }

    return response.data;
};

export const scheduleMeeting = async (title: string, date: string) => {
    const response = await api.post('/meetings/schedule', { title, date });
    return response.data;
};

export const endMeeting = async (id: string) => {
    const response = await api.post(`/meetings/${id}/end`);
    return response.data;
};

export const deleteMeeting = async (id: number) => {
    const response = await api.delete(`/meetings/${id}`);
    return response.data;
};

export const fetchTasks = async (): Promise<Task[]> => {
    const response = await api.get('/tasks');
    return response.data;
};

export const updateTaskStatus = async (taskId: number, status: string) => {
    const response = await api.put(`/tasks/${taskId}`, { status });
    return response.data;
};
