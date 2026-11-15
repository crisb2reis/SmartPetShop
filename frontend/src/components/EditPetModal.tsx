import React, { useState, useEffect } from 'react';
import { X, Dog, User, Calendar, Scale, FileText, AlertCircle, Check } from 'lucide-react';
import { updatePet, Pet, Tutor } from '../services/api';

interface EditPetModalProps {
  isOpen: boolean;
  pet: Pet | null;
  tutors: Tutor[];
  onClose: () => void;
  onSuccess: (updatedPet: Pet) => void;
}

export const EditPetModal: React.FC<EditPetModalProps> = ({
  isOpen,
  pet,
  tutors,
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState('');
  const [species, setSpecies] = useState('Canino');
  const [breed, setBreed] = useState('');
  const [tutorId, setTutorId] = useState('');
  const [weight, setWeight] = useState<string>('');
  const [birthDate, setBirthDate] = useState<string>('');
  const [medicalNotes, setMedicalNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (pet) {
      setName(pet.name || '');
      setSpecies(pet.species || 'Canino');
      setBreed(pet.breed || '');
      setTutorId(pet.tutor_id || (tutors.length > 0 ? tutors[0].id : ''));
      setWeight(pet.weight !== undefined && pet.weight !== null ? String(pet.weight) : '');
      setBirthDate(pet.birth_date ? pet.birth_date.split('T')[0] : '');
      setMedicalNotes(pet.medical_notes || '');
      setError(null);
    }
  }, [pet, isOpen, tutors]);

  if (!isOpen || !pet) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('O nome do pet é obrigatório.');
      return;
    }
    if (!tutorId) {
      setError('O pet deve obrigatoriamente estar vinculado a um tutor.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const updated = await updatePet(pet.id, {
        name: name.trim(),
        species,
        breed: breed.trim() || undefined,
        tutor_id: tutorId,
        weight: weight ? parseFloat(weight) : undefined,
        birth_date: birthDate || undefined,
        medical_notes: medicalNotes.trim() || undefined,
      });

      onSuccess(updated);
      onClose();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Erro ao atualizar dados do pet.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center">
              <Dog className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-800">Editar Dados do Pet</h3>
              <p className="text-xs text-slate-500">Altere informações cadastrais e vínculo com o tutor</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-start space-x-2 text-xs text-red-700">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Vínculo Obrigatório com o Tutor */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Tutor Proprietário (Vínculo Obrigatório) *
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
              <select
                value={tutorId}
                onChange={(e) => setTutorId(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-semibold text-slate-800"
                required
              >
                <option value="">Selecione um tutor...</option>
                {tutors.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({t.phone})
                  </option>
                ))}
              </select>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Todo animal deve impreterivelmente pertencer a um tutor cadastrado.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Nome do Pet */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Nome do Pet *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ex: Bob, Mel, Thor"
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium text-slate-800"
                required
              />
            </div>

            {/* Espécie */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Espécie *
              </label>
              <select
                value={species}
                onChange={(e) => setSpecies(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium text-slate-800"
                required
              >
                <option value="Canino">Canino (Cachorro)</option>
                <option value="Felino">Felino (Gato)</option>
                <option value="Ave">Ave</option>
                <option value="Outro">Outro</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Raça */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Raça
              </label>
              <input
                type="text"
                value={breed}
                onChange={(e) => setBreed(e.target.value)}
                placeholder="Ex: Shih Tzu, SRD"
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all text-slate-800"
              />
            </div>

            {/* Peso */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Scale className="w-3.5 h-3.5 text-slate-400" />
                Peso (kg)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="150"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                placeholder="Ex: 8.5"
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all text-slate-800"
              />
            </div>

            {/* Data de Nascimento */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                Nascimento
              </label>
              <input
                type="date"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all text-slate-800"
              />
            </div>
          </div>

          {/* Observações Médicas / Cuidados */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
              <FileText className="w-3.5 h-3.5 text-slate-400" />
              Observações Médicas / Cuidados Especiais
            </label>
            <textarea
              rows={2}
              value={medicalNotes}
              onChange={(e) => setMedicalNotes(e.target.value)}
              placeholder="Ex: Alergia a shampoo perfumado; dócil; cuidados na tosa com as orelhas..."
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all text-slate-800"
            />
          </div>

          {/* Footer Buttons */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-sm transition-all flex items-center space-x-1.5 disabled:opacity-50"
            >
              <Check className="w-4 h-4" />
              <span>{loading ? 'Salvando...' : 'Salvar Alterações'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

