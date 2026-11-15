import axios from 'axios';

export const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
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

export const fetchSystemStatus = async (): Promise<SystemStatus> => {
  const response = await axios.get('http://localhost:8000/');
  return response.data;
};

export const sendChatMessage = async (content: string, sessionId?: string) => {
  const response = await api.post('/chat/message', {
    content,
    session_id: sessionId || null,
    channel: 'web'
  });
  return response.data;
};

export const fetchAlerts = async (status: string = 'pending'): Promise<AlertItem[]> => {
  const response = await api.get('/alerts', {
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
