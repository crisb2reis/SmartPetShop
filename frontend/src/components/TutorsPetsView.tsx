import React, { useState, useEffect } from 'react';
import { User, Dog, Plus, Search, Phone, Mail, CheckCircle, AlertCircle, Pencil } from 'lucide-react';
import { fetchTutors, fetchPets, createTutor, createPet, Tutor, Pet } from '../services/api';
import { EditTutorModal } from './EditTutorModal';

export const TutorsPetsView: React.FC = () => {
  const [tutors, setTutors] = useState<Tutor[]>([]);
  const [pets, setPets] = useState<Pet[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Edit tutor modal state
  const [editingTutor, setEditingTutor] = useState<Tutor | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // Form states
  const [showTutorForm, setShowTutorForm] = useState(false);
  const [showPetForm, setShowPetForm] = useState(false);
  const [tutorName, setTutorName] = useState('');
  const [tutorPhone, setTutorPhone] = useState('');
  const [tutorEmail, setTutorEmail] = useState('');

  const [petTutorId, setPetTutorId] = useState('');
  const [petName, setPetName] = useState('');
  const [petSpecies, setPetSpecies] = useState('Canino');
  const [petBreed, setPetBreed] = useState('');

  const [message, setMessage] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [tutorsData, petsData] = await Promise.all([fetchTutors(), fetchPets()]);
      setTutors(tutorsData);
      setPets(petsData);
      if (tutorsData.length > 0) setPetTutorId(tutorsData[0].id);
    } catch (err) {
      console.error('Erro ao carregar tutores/pets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateTutor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tutorName || !tutorPhone) return;
    try {
      await createTutor({
        name: tutorName,
        phone: tutorPhone,
        email: tutorEmail || undefined,
      });
      setMessage('Tutor cadastrado com sucesso!');
      setTutorName('');
      setTutorPhone('');
      setTutorEmail('');
      setShowTutorForm(false);
      await loadData();
    } catch (err: any) {
      setMessage(`Erro: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleCreatePet = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!petTutorId || !petName || !petSpecies) return;
    try {
      await createPet({
        tutor_id: petTutorId,
        name: petName,
        species: petSpecies,
        breed: petBreed || undefined,
      });
      setMessage('Pet cadastrado com sucesso!');
      setPetName('');
      setPetBreed('');
      setShowPetForm(false);
      await loadData();
    } catch (err: any) {
      setMessage(`Erro: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleOpenEditTutor = (tutor: Tutor) => {
    setEditingTutor(tutor);
    setIsEditModalOpen(true);
  };

  const handleEditSuccess = (updatedTutor: Tutor) => {
    setTutors((prev) => prev.map((t) => (t.id === updatedTutor.id ? updatedTutor : t)));
    setMessage(`Tutor ${updatedTutor.name} atualizado com sucesso!`);
  };

  const filteredTutors = tutors.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.phone.includes(search)
  );

  return (
    <div className="space-y-6">
      {/* Header & Quick Actions */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <User className="w-5 h-5 text-emerald-600" />
            Gestão de Tutores & Pets
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Cadastros rápidos de novos clientes e seus animais para atendimento na recepção
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowTutorForm(!showTutorForm)}
            className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Novo Tutor</span>
          </button>
          <button
            onClick={() => setShowPetForm(!showPetForm)}
            className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-900 text-white transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Novo Pet</span>
          </button>
        </div>
      </div>

      {message && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center justify-between">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="text-xs font-bold">&times;</button>
        </div>
      )}

      {/* Tutor Creation Form Inline */}
      {showTutorForm && (
        <form onSubmit={handleCreateTutor} className="bg-emerald-50 border border-emerald-200 rounded-2xl p-5 space-y-3">
          <h3 className="text-sm font-bold text-emerald-900">Cadastrar Novo Tutor</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input
              type="text"
              placeholder="Nome completo"
              value={tutorName}
              onChange={(e) => setTutorName(e.target.value)}
              className="px-3 py-2 text-sm bg-white border border-emerald-300 rounded-xl focus:outline-none"
              required
            />
            <input
              type="text"
              placeholder="Telefone / WhatsApp (ex: 11999998888)"
              value={tutorPhone}
              onChange={(e) => setTutorPhone(e.target.value)}
              className="px-3 py-2 text-sm bg-white border border-emerald-300 rounded-xl focus:outline-none"
              required
            />
            <input
              type="email"
              placeholder="E-mail (opcional)"
              value={tutorEmail}
              onChange={(e) => setTutorEmail(e.target.value)}
              className="px-3 py-2 text-sm bg-white border border-emerald-300 rounded-xl focus:outline-none"
            />
          </div>
          <div className="flex justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={() => setShowTutorForm(false)}
              className="px-3 py-1.5 text-xs font-semibold text-emerald-800 hover:bg-emerald-100 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 text-xs font-bold text-white bg-emerald-700 hover:bg-emerald-800 rounded-lg shadow-sm"
            >
              Salvar Tutor
            </button>
          </div>
        </form>
      )}

      {/* Pet Creation Form Inline */}
      {showPetForm && (
        <form onSubmit={handleCreatePet} className="bg-slate-100 border border-slate-200 rounded-2xl p-5 space-y-3">
          <h3 className="text-sm font-bold text-slate-800">Cadastrar Novo Pet</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <select
              value={petTutorId}
              onChange={(e) => setPetTutorId(e.target.value)}
              className="px-3 py-2 text-sm bg-white border border-slate-300 rounded-xl focus:outline-none"
              required
            >
              {tutors.map((t) => (
                <option key={t.id} value={t.id}>
                  Tutor: {t.name}
                </option>
              ))}
            </select>
            <input
              type="text"
              placeholder="Nome do pet (ex: Bob, Mel)"
              value={petName}
              onChange={(e) => setPetName(e.target.value)}
              className="px-3 py-2 text-sm bg-white border border-slate-300 rounded-xl focus:outline-none"
              required
            />
            <select
              value={petSpecies}
              onChange={(e) => setPetSpecies(e.target.value)}
              className="px-3 py-2 text-sm bg-white border border-slate-300 rounded-xl focus:outline-none"
            >
              <option value="Canino">Canino (Cachorro)</option>
              <option value="Felino">Felino (Gato)</option>
              <option value="Ave">Ave</option>
              <option value="Outro">Outro</option>
            </select>
            <input
              type="text"
              placeholder="Raça (ex: Shih Tzu, SRD)"
              value={petBreed}
              onChange={(e) => setPetBreed(e.target.value)}
              className="px-3 py-2 text-sm bg-white border border-slate-300 rounded-xl focus:outline-none"
            />
          </div>
          <div className="flex justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={() => setShowPetForm(false)}
              className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-200 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 text-xs font-bold text-white bg-slate-800 hover:bg-slate-900 rounded-lg shadow-sm"
            >
              Salvar Pet
            </button>
          </div>
        </form>
      )}

      {/* Tutors & Pets List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTutors.map((t) => {
          const tutorPets = pets.filter((p) => p.tutor_id === t.id);
          return (
            <div key={t.id} className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center space-x-3 min-w-0 flex-1">
                  <div className="w-9 h-9 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-sm shrink-0">
                    {t.name.substring(0, 2).toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <h4 className="text-sm font-bold text-slate-800 truncate">{t.name}</h4>
                    <p className="text-xs text-slate-500 flex items-center gap-1">
                      <Phone className="w-3 h-3 text-emerald-600 shrink-0" />
                      <span>{t.phone}</span>
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => handleOpenEditTutor(t)}
                  title="Editar dados do tutor"
                  className="p-1.5 text-slate-400 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors border border-transparent hover:border-emerald-200 shrink-0"
                >
                  <Pencil className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Pets do Tutor */}
              <div className="pt-2 border-t border-slate-100 space-y-1.5">
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Pets ({tutorPets.length}):</p>
                {tutorPets.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">Nenhum pet cadastrado.</p>
                ) : (
                  <div className="flex flex-wrap gap-1.5">
                    {tutorPets.map((p) => (
                      <span
                        key={p.id}
                        className="text-xs font-semibold bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg flex items-center gap-1"
                      >
                        <Dog className="w-3 h-3 text-emerald-600" />
                        {p.name} <span className="text-[10px] text-slate-400 font-normal">({p.breed || p.species})</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal de Edição de Tutor */}
      <EditTutorModal
        isOpen={isEditModalOpen}
        tutor={editingTutor}
        onClose={() => {
          setIsEditModalOpen(false);
          setEditingTutor(null);
        }}
        onSuccess={handleEditSuccess}
      />
    </div>
  );
};

