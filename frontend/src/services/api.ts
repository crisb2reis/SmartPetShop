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
  description?: string;
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
export const fetchServices = async (category?: string, activeOnly: boolean = true): Promise<ServiceItem[]> => {
  const params: Record<string, any> = { active_only: activeOnly };
  if (category) params.category = category;
  const response = await api.get('/services/', { params });
  return response.data;
};

export const createService = async (data: {
  name: string;
  category: string;
  price: number;
  duration_minutes: number;
  description?: string;
  active?: boolean;
}): Promise<ServiceItem> => {
  const response = await api.post('/services/', data);
  return response.data;
};

export const updateService = async (
  serviceId: string,
  data: Partial<ServiceItem>
): Promise<ServiceItem> => {
  const response = await api.put(`/services/${serviceId}`, data);
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

// ============================================================
// Vacinas & Carteirinha Digital (Conformidade CFMV)
// ============================================================
export interface VaccineCatalogItem {
  id: string;
  species: string;
  name: string;
  type: 'OBRIGATORIA' | 'OPCIONAL';
  recommended_age_weeks: number;
  doses_required: number;
  booster_interval_days: number;
  description?: string;
}

export interface VaccineBatchItem {
  id: string;
  vaccine_catalog_id: string;
  batch_number: string;
  manufacturer: string;
  expiration_date: string;
  active: boolean;
  vaccine_catalog?: VaccineCatalogItem;
}

export interface VaccineRecordItem {
  id: string;
  tenant_id: string;
  pet_id: string;
  vaccine_catalog_id: string;
  vaccine_batch_id?: string;
  application_date: string;
  next_due_date?: string;
  vet_name: string;
  vet_crmv: string;
  clinic_id?: string;
  status: 'APLICADA' | 'PENDENTE' | 'ATRASADA';
  notes?: string;
  vaccine_catalog?: VaccineCatalogItem;
  vaccine_batch?: VaccineBatchItem;
}

export interface VaccineCardData {
  pet_id: string;
  pet_name: string;
  species: string;
  breed?: string;
  total_applied: number;
  due_soon_count: number;
  overdue_count: number;
  applied_records: VaccineRecordItem[];
  upcoming_records: VaccineRecordItem[];
  all_records: VaccineRecordItem[];
}

export const fetchVaccineCatalogs = async (species?: string): Promise<VaccineCatalogItem[]> => {
  const params: Record<string, string> = {};
  if (species) params.species = species;
  const response = await api.get('/vaccine-catalogs/', { params });
  return response.data;
};

export const createVaccineCatalog = async (data: {
  species: string;
  name: string;
  type: string;
  recommended_age_weeks: number;
  doses_required: number;
  booster_interval_days: number;
  description?: string;
}): Promise<VaccineCatalogItem> => {
  const response = await api.post('/vaccine-catalogs/', data);
  return response.data;
};

export const fetchVaccineBatches = async (catalogId?: string, activeOnly: boolean = false): Promise<VaccineBatchItem[]> => {
  const params: Record<string, any> = { active_only: activeOnly };
  if (catalogId) params.catalog_id = catalogId;
  const response = await api.get('/vaccine-batches/', { params });
  return response.data;
};

export const createVaccineBatch = async (data: {
  vaccine_catalog_id: string;
  batch_number: string;
  manufacturer: string;
  expiration_date: string;
  active?: boolean;
}): Promise<VaccineBatchItem> => {
  const response = await api.post('/vaccine-batches/', data);
  return response.data;
};

export const fetchPetVaccinations = async (petId: string): Promise<VaccineRecordItem[]> => {
  const response = await api.get(`/pets/${petId}/vaccinations/`);
  return response.data;
};

export const fetchPetVaccinationCard = async (petId: string): Promise<VaccineCardData> => {
  const response = await api.get(`/pets/${petId}/vaccinations/card`);
  return response.data;
};

export const createPetVaccination = async (
  petId: string,
  data: {
    vaccine_catalog_id: string;
    vaccine_batch_id?: string;
    application_date: string;
    next_due_date?: string;
    vet_name: string;
    vet_crmv: string;
    notes?: string;
  }
): Promise<VaccineRecordItem> => {
  const response = await api.post(`/pets/${petId}/vaccinations/`, data);
  return response.data;
};

export const updatePetVaccination = async (
  petId: string,
  recordId: string,
  data: Partial<VaccineRecordItem>
): Promise<VaccineRecordItem> => {
  const response = await api.put(`/pets/${petId}/vaccinations/${recordId}`, data);
  return response.data;
};
