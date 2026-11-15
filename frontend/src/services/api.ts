import axios from 'axios';

const getHost = () => {
  if (typeof window !== 'undefined' && window.location.hostname) {
    return window.location.hostname;
  }
  return 'localhost';
};

export const API_HOST_URL = `http://${getHost()}:8001`;

export const api = axios.create({
  baseURL: `${API_HOST_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface SystemStatus {
  system: string;
  version: string;
  status: string;
  docs: string;
}

export interface Tutor {
  id: string;
  name: string;
  phone: string;
  email?: string;
  address?: string;
}

export interface Pet {
  id: string;
  tutor_id: string;
  name: string;
  species: string;
  breed?: string;
  weight?: number;
  birth_date?: string;
  medical_notes?: string;
}

export interface ServiceItem {
  id: string;
  name: string;
  category: string;
  price: number;
  duration_minutes: number;
  active: boolean;
}

export interface AppointmentItem {
  id: string;
  pet_id: string;
  service_id: string;
  scheduled_at: string;
  status: 'scheduled' | 'in_progress' | 'completed' | 'canceled';
  notes?: string;
  pet?: Pet;
  service?: ServiceItem;
}

export interface AlertItem {
  id: string;
  tutor_id: string;
  pet_id: string;
  alert_type: string;
  message: string;
  status: 'pending' | 'sent' | 'clicked' | 'dismissed';
  scheduled_for: string;
  pet?: {
    name: string;
    species: string;
    breed?: string;
  };
  tutor?: {
    name: string;
    phone: string;
  };
}

// System
export const fetchSystemStatus = async (): Promise<SystemStatus> => {
  const response = await axios.get(`${API_HOST_URL}/`);
  return response.data;
};

// Chat
export const sendChatMessage = async (content: string, sessionId?: string) => {
  const response = await api.post('/chat/message', {
    content,
    session_id: sessionId || null,
    channel: 'web'
  });
  return response.data;
};

// Appointments
export const fetchAppointments = async (targetDate?: string, status?: string): Promise<AppointmentItem[]> => {
  const params: Record<string, string> = {};
  if (targetDate) params.target_date = targetDate;
  if (status && status !== 'all') params.status = status;
  const response = await api.get('/appointments/', { params });
  return response.data;
};

export const createAppointment = async (data: {
  pet_id: string;
  service_id: string;
  scheduled_at: string;
  notes?: string;
}): Promise<AppointmentItem> => {
  const response = await api.post('/appointments/', data);
  return response.data;
};

export const updateAppointmentStatus = async (
  appointmentId: string,
  newStatus: 'scheduled' | 'in_progress' | 'completed' | 'canceled'
): Promise<AppointmentItem> => {
  const response = await api.put(`/appointments/${appointmentId}`, {
    status: newStatus
  });
  return response.data;
};

// Services & Pets & Tutors
export const fetchServices = async (): Promise<ServiceItem[]> => {
  const response = await api.get('/services/', { params: { active_only: true } });
  return response.data;
};

export const fetchPets = async (): Promise<Pet[]> => {
  const response = await api.get('/pets/');
  return response.data;
};

export const fetchTutors = async (): Promise<Tutor[]> => {
  const response = await api.get('/tutors/');
  return response.data;
};

export const createTutor = async (data: { name: string; phone: string; email?: string }): Promise<Tutor> => {
  const response = await api.post('/tutors/', data);
  return response.data;
};

export const updateTutor = async (
  tutorId: string,
  data: { name?: string; phone?: string; email?: string; address?: string }
): Promise<Tutor> => {
  const response = await api.put(`/tutors/${tutorId}`, data);
  return response.data;
};

export const createPet = async (data: {
  tutor_id: string;
  name: string;
  species: string;
  breed?: string;
  weight?: number;
  birth_date?: string;
  medical_notes?: string;
}): Promise<Pet> => {
  const response = await api.post('/pets/', data);
  return response.data;
};

export const updatePet = async (
  petId: string,
  data: {
    tutor_id?: string;
    name?: string;
    species?: string;
    breed?: string;
    weight?: number;
    birth_date?: string;
    medical_notes?: string;
  }
): Promise<Pet> => {
  const response = await api.put(`/pets/${petId}`, data);
  return response.data;
};

// Alerts
export const fetchAlerts = async (status: string = 'pending'): Promise<AlertItem[]> => {
  const response = await api.get('/alerts/', {
    params: { status }
  });
  return response.data;
};

export const runAlertScan = async (): Promise<{ total_pets_analyzed: number; alerts_generated: number; alerts: AlertItem[] }> => {
  const response = await api.post('/alerts/run-scan');
  return response.data;
};

export const updateAlertStatus = async (alertId: string, newStatus: string): Promise<AlertItem> => {
  const response = await api.patch(`/alerts/${alertId}/status`, {
    status: newStatus
  });
  return response.data;
};
