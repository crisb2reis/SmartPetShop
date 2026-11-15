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
