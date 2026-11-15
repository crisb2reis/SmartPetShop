import React, { useState, useEffect } from 'react';
import { X, Calendar, Clock, Dog, Scissors, AlertCircle } from 'lucide-react';
import { fetchPets, fetchServices, createAppointment, Pet, ServiceItem } from '../services/api';

interface NewAppointmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const NewAppointmentModal: React.FC<NewAppointmentModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [pets, setPets] = useState<Pet[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [selectedPet, setSelectedPet] = useState('');
  const [selectedService, setSelectedService] = useState('');
  const [dateStr, setDateStr] = useState(new Date().toISOString().split('T')[0]);
  const [timeStr, setTimeStr] = useState('09:00');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      Promise.all([fetchPets(), fetchServices()])
        .then(([petsData, servicesData]) => {
          setPets(petsData);
          setServices(servicesData);
          if (petsData.length > 0) setSelectedPet(petsData[0].id);
          if (servicesData.length > 0) setSelectedService(servicesData[0].id);
        })
        .catch((err) => console.error('Erro ao carregar pets/serviços:', err));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPet || !selectedService || !dateStr || !timeStr) {
      setError('Por favor preencha todos os campos obrigatórios.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const scheduledAtIso = `${dateStr}T${timeStr}:00`;
      await createAppointment({
        pet_id: selectedPet,
        service_id: selectedService,
        scheduled_at: scheduledAtIso,
        notes: notes.trim() || undefined,
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Erro ao realizar agendamento.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 bg-emerald-600 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <Calendar className="w-5 h-5" />
            <h3 className="font-bold text-base">Novo Agendamento</h3>
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Seleção de Pet */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Dog className="w-3.5 h-3.5 text-emerald-600" />
              Pet
            </label>
            {pets.length === 0 ? (
              <p className="text-xs text-amber-600 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                Nenhum pet cadastrado no sistema ainda. Cadastre um tutor e pet primeiro.
              </p>
            ) : (
              <select
                value={selectedPet}
                onChange={(e) => setSelectedPet(e.target.value)}
                className="w-full border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm bg-slate-50 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                {pets.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.species} {p.breed ? `- ${p.breed}` : ''})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Seleção de Serviço */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Scissors className="w-3.5 h-3.5 text-emerald-600" />
              Serviço
            </label>
            {services.length === 0 ? (
              <p className="text-xs text-amber-600 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                Nenhum serviço ativo cadastrado.
              </p>
            ) : (
              <select
                value={selectedService}
                onChange={(e) => setSelectedService(e.target.value)}
                className="w-full border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm bg-slate-50 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                {services.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} - R$ {Number(s.price).toFixed(2)} ({s.duration_minutes} min)
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Data e Hora */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-emerald-600" />
                Data
              </label>
              <input
                type="date"
                value={dateStr}
                onChange={(e) => setDateStr(e.target.value)}
                className="w-full border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm bg-slate-50 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-emerald-600" />
                Horário
              </label>
              <input
                type="time"
                value={timeStr}
                onChange={(e) => setTimeStr(e.target.value)}
                className="w-full border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm bg-slate-50 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Observações */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Observações (Opcional)
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ex: Tosa higiênica baixa, pet com medo de secador..."
              className="w-full border border-slate-200 rounded-xl p-3 text-sm bg-slate-50 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
          </div>

          {/* Ações */}
          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-xl text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50"
            >
              {loading ? 'Confirmando...' : 'Confirmar Agendamento'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
