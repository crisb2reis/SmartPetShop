import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  Dog,
  Plus,
  Play,
  CheckCircle,
  XCircle,
  RefreshCw
} from 'lucide-react';
import {
  fetchAppointments,
  updateAppointmentStatus,
  AppointmentItem
} from '../services/api';
import { NewAppointmentModal } from './NewAppointmentModal';

export const AppointmentsDashboard: React.FC = () => {
  const [appointments, setAppointments] = useState<AppointmentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadAppointments = async () => {
    setLoading(true);
    try {
      const data = await fetchAppointments(selectedDate, statusFilter);
      setAppointments(data);
    } catch (err) {
      console.error('Erro ao buscar agendamentos:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppointments();
  }, [selectedDate, statusFilter]);

  const handleStatusChange = async (
    id: string,
    newStatus: 'scheduled' | 'in_progress' | 'completed' | 'canceled'
  ) => {
    try {
      await updateAppointmentStatus(id, newStatus);
      await loadAppointments();
    } catch (err) {
      console.error('Erro ao atualizar status:', err);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'scheduled':
        return { label: 'Agendado', bg: 'bg-blue-50 text-blue-700 border-blue-200' };
      case 'in_progress':
        return { label: 'Em Atendimento', bg: 'bg-amber-50 text-amber-700 border-amber-200' };
      case 'completed':
        return { label: 'Concluído', bg: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
      case 'canceled':
        return { label: 'Cancelado', bg: 'bg-slate-100 text-slate-500 border-slate-200' };
      default:
        return { label: status, bg: 'bg-slate-50 text-slate-700 border-slate-200' };
    }
  };

  // Metrics
  const totalCount = appointments.length;
  const scheduledCount = appointments.filter((a) => a.status === 'scheduled').length;
  const inProgressCount = appointments.filter((a) => a.status === 'in_progress').length;
  const completedCount = appointments.filter((a) => a.status === 'completed').length;

  return (
    <div className="space-y-6">
      {/* Top Controls & Metrics */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-emerald-600" />
              Recepção & Grade de Atendimentos
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Gerencie a entrada, fluxo de banho/tosa e consultas do dia em tempo real
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsModalOpen(true)}
              className="flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>Novo Agendamento</span>
            </button>
            <button
              onClick={loadAppointments}
              className="p-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-100 transition-colors"
              title="Atualizar agenda"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-600' : ''}`} />
            </button>
          </div>
        </div>

        {/* Filters and Date Picker */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-slate-500">Data:</span>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="text-xs font-medium border border-slate-200 rounded-lg px-2.5 py-1.5 bg-slate-50 text-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <button
              onClick={() => setSelectedDate(new Date().toISOString().split('T')[0])}
              className="text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
            >
              Hoje
            </button>
          </div>

          {/* Status Tabs */}
          <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
            {[
              { id: 'all', label: `Todos (${totalCount})` },
              { id: 'scheduled', label: `Agendados (${scheduledCount})` },
              { id: 'in_progress', label: `Em Atendimento (${inProgressCount})` },
              { id: 'completed', label: `Concluídos (${completedCount})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`px-3 py-1 rounded-lg transition-all ${
                  statusFilter === tab.id
                    ? 'bg-white text-slate-800 shadow-sm font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Appointment Cards / List */}
      <div className="space-y-3">
        {loading ? (
          <div className="text-center py-12 bg-white rounded-2xl border border-slate-200">
            <RefreshCw className="w-6 h-6 animate-spin text-emerald-600 mx-auto mb-2" />
            <p className="text-xs text-slate-500">Carregando agendamentos do dia...</p>
          </div>
        ) : appointments.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-2xl border border-slate-200 p-6 space-y-3">
            <Calendar className="w-10 h-10 text-slate-300 mx-auto" />
            <div>
              <p className="text-sm font-bold text-slate-700">Nenhum atendimento encontrado para esta data</p>
              <p className="text-xs text-slate-400 mt-1">
                A grade está livre para novos agendamentos ou consulte outra data.
              </p>
            </div>
            <button
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center space-x-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-3.5 py-2 rounded-xl border border-emerald-200 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Agendar primeiro atendimento</span>
            </button>
          </div>
        ) : (
          appointments.map((appt) => {
            const badge = getStatusBadge(appt.status);
            const timeFormatted = new Date(appt.scheduled_at).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            });

            return (
              <div
                key={appt.id}
                className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:border-slate-300 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                {/* Left: Time and Service Info */}
                <div className="flex items-start space-x-4">
                  <div className="flex flex-col items-center justify-center bg-slate-100 rounded-xl px-3 py-2 text-center min-w-[70px]">
                    <Clock className="w-4 h-4 text-emerald-600 mb-0.5" />
                    <span className="text-sm font-bold text-slate-800">{timeFormatted}</span>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-slate-800 text-sm">
                        {appt.service?.name || 'Serviço'}
                      </span>
                      <span className="text-[11px] px-2 py-0.5 rounded-full font-bold bg-slate-100 text-slate-600">
                        {appt.service?.category || 'Geral'}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${badge.bg}`}>
                        {badge.label}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 text-xs text-slate-600">
                      <Dog className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="font-semibold text-slate-800">
                        {appt.pet?.name || 'Pet'}
                      </span>
                      <span className="text-slate-400">&bull;</span>
                      <span>
                        {appt.pet?.species} {appt.pet?.breed ? `(${appt.pet.breed})` : ''}
                      </span>
                    </div>

                    {appt.notes && (
                      <p className="text-xs text-slate-500 italic">
                        "{appt.notes}"
                      </p>
                    )}
                  </div>
                </div>

                {/* Right: Actions / Status transitions */}
                <div className="flex items-center space-x-2 self-end md:self-center">
                  {appt.status === 'scheduled' && (
                    <button
                      onClick={() => handleStatusChange(appt.id, 'in_progress')}
                      className="inline-flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white transition-colors shadow-sm"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                      <span>Iniciar Atendimento</span>
                    </button>
                  )}

                  {appt.status === 'in_progress' && (
                    <button
                      onClick={() => handleStatusChange(appt.id, 'completed')}
                      className="inline-flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white transition-colors shadow-sm"
                    >
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>Concluir</span>
                    </button>
                  )}

                  {appt.status !== 'canceled' && appt.status !== 'completed' && (
                    <button
                      onClick={() => handleStatusChange(appt.id, 'canceled')}
                      className="inline-flex items-center space-x-1 text-xs font-semibold px-2.5 py-1.5 rounded-xl text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                      title="Cancelar agendamento"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Cancelar</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Modal de Novo Agendamento */}
      <NewAppointmentModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={loadAppointments}
      />
    </div>
  );
};

