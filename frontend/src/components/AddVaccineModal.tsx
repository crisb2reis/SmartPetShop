import React, { useState, useEffect } from 'react';
import {
  X,
  Syringe,
  Calendar,
  Clock,
  User,
  ShieldCheck,
  AlertCircle,
  Check,
  Layers,
  FileText
} from 'lucide-react';
import {
  fetchVaccineCatalogs,
  fetchVaccineBatches,
  createPetVaccination,
  VaccineCatalogItem,
  VaccineBatchItem,
  Pet
} from '../services/api';
import { NewVaccineCatalogModal } from './NewVaccineCatalogModal';
import { NewVaccineBatchModal } from './NewVaccineBatchModal';

interface AddVaccineModalProps {
  isOpen: boolean;
  pet: Pet | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const AddVaccineModal: React.FC<AddVaccineModalProps> = ({
  isOpen,
  pet,
  onClose,
  onSuccess,
}) => {
  const [catalogs, setCatalogs] = useState<VaccineCatalogItem[]>([]);
  const [batches, setBatches] = useState<VaccineBatchItem[]>([]);
  const [selectedCatalogId, setSelectedCatalogId] = useState<string>('');
  const [selectedBatchId, setSelectedBatchId] = useState<string>('');
  const [applicationDate, setApplicationDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [nextDueDate, setNextDueDate] = useState<string>('');
  const [vetName, setVetName] = useState('Dr. Roberto Alencar');
  const [vetCrmv, setVetCrmv] = useState('CRMV-SP 38412');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Quick modals state
  const [isNewVaccineOpen, setIsNewVaccineOpen] = useState(false);
  const [isNewBatchOpen, setIsNewBatchOpen] = useState(false);

  // 1. Carregar catálogo oficial de acordo com a espécie do pet
  useEffect(() => {
    if (isOpen && pet) {
      setError(null);
      fetchVaccineCatalogs(pet.species)
        .then((data) => {
          setCatalogs(data);
          if (data.length > 0) {
            setSelectedCatalogId(data[0].id);
          }
        })
        .catch((err) => {
          console.error('Erro ao carregar catálogo de vacinas:', err);
          setError('Não foi possível carregar as vacinas do catálogo.');
        });
    }
  }, [isOpen, pet]);

  // 2. Quando seleciona uma vacina, busca os lotes ativos e calcula o próximo reforço sugerido
  useEffect(() => {
    if (!selectedCatalogId) return;

    const catalog = catalogs.find((c) => c.id === selectedCatalogId);
    if (catalog) {
      // Calcular next_due_date sugerida
      const appDate = new Date(applicationDate);
      if (!isNaN(appDate.getTime())) {
        const boosterDays = catalog.booster_interval_days || 365;
        const suggestedDue = new Date(appDate);
        suggestedDue.setDate(suggestedDue.getDate() + boosterDays);
        setNextDueDate(suggestedDue.toISOString().split('T')[0]);
      }

      // Buscar lotes correspondentes
      fetchVaccineBatches(selectedCatalogId)
        .then((batchList) => {
          setBatches(batchList);
          if (batchList.length > 0) {
            setSelectedBatchId(batchList[0].id);
          } else {
            setSelectedBatchId('');
          }
        })
        .catch((err) => console.error('Erro ao buscar lotes:', err));
    }
  }, [selectedCatalogId, applicationDate, catalogs]);

  const handleVaccineCreated = (newCat: VaccineCatalogItem) => {
    setCatalogs((prev) => [newCat, ...prev]);
    setSelectedCatalogId(newCat.id);
  };

  const handleBatchCreated = (newBatch: VaccineBatchItem) => {
    setBatches((prev) => [newBatch, ...prev]);
    setSelectedBatchId(newBatch.id);
  };

  if (!isOpen || !pet) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCatalogId) {
      setError('Selecione uma vacina do catálogo.');
      return;
    }
    if (!vetName.trim() || !vetCrmv.trim()) {
      setError('Nome e CRMV do médico veterinário são obrigatórios (Norma CFMV).');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await createPetVaccination(pet.id, {
        vaccine_catalog_id: selectedCatalogId,
        vaccine_batch_id: selectedBatchId || undefined,
        application_date: applicationDate,
        next_due_date: nextDueDate || undefined,
        vet_name: vetName.trim(),
        vet_crmv: vetCrmv.trim(),
        notes: notes.trim() || undefined,
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Erro ao registrar vacina.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const selectedCatalog = catalogs.find((c) => c.id === selectedCatalogId);

  return (
    <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-lg w-full overflow-hidden flex flex-col max-h-[92vh]">
        {/* Modal Header */}
        <div className="px-6 py-4.5 bg-gradient-to-r from-emerald-600 to-teal-600 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center shadow-inner">
              <Syringe className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Lançar Nova Aplicação</h3>
              <p className="text-xs text-emerald-100">
                Paciente: <strong>{pet.name}</strong> ({pet.species})
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white p-1.5 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-start space-x-2 text-xs text-red-700">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Seleção do Catálogo Oficial */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Vacina Oficial ({pet.species}) *
              </label>
              <button
                type="button"
                onClick={() => setIsNewVaccineOpen(true)}
                className="text-[11px] font-bold text-emerald-600 hover:text-emerald-700 hover:underline"
              >
                + Nova Vacina
              </button>
            </div>
            <div className="relative">
              <Syringe className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
              <select
                value={selectedCatalogId}
                onChange={(e) => setSelectedCatalogId(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-semibold text-slate-800"
                required
              >
                {catalogs.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} - [{c.type}]
                  </option>
                ))}
              </select>
            </div>
            {selectedCatalog?.description && (
              <p className="text-[11px] text-slate-500 mt-1 italic">
                {selectedCatalog.description}
              </p>
            )}
          </div>

          {/* Seleção de Lote do Estoque */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Lote / Ampola em Estoque
              </label>
              <button
                type="button"
                onClick={() => setIsNewBatchOpen(true)}
                className="text-[11px] font-bold text-teal-600 hover:text-teal-700 hover:underline"
              >
                + Novo Lote Ampola
              </button>
            </div>
            <div className="relative">
              <Layers className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
              <select
                value={selectedBatchId}
                onChange={(e) => setSelectedBatchId(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium text-slate-800"
              >
                <option value="">Sem lote específico (ou aplicação externa)</option>
                {batches.map((b) => (
                  <option key={b.id} value={b.id}>
                    Lote: {b.batch_number} - {b.manufacturer} (Val: {b.expiration_date})
                  </option>
                ))}
              </select>
            </div>
            {batches.length === 0 && (
              <p className="text-[11px] text-amber-600 mt-1">
                Nenhum lote ativo cadastrado no estoque local para esta vacina.
              </p>
            )}
          </div>

          {/* Datas: Aplicação e Próximo Reforço */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-emerald-600" />
                Data da Aplicação *
              </label>
              <input
                type="date"
                value={applicationDate}
                onChange={(e) => setApplicationDate(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-semibold text-slate-800"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-amber-600" />
                Próximo Reforço (Sugerido) *
              </label>
              <input
                type="date"
                value={nextDueDate}
                onChange={(e) => setNextDueDate(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-semibold text-slate-800"
                required
              />
            </div>
          </div>

          {/* Dados do Médico Veterinário (Exigência CFMV) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-slate-100">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <User className="w-3.5 h-3.5 text-slate-400" />
                Médico Veterinário *
              </label>
              <input
                type="text"
                value={vetName}
                onChange={(e) => setVetName(e.target.value)}
                placeholder="Ex: Dra. Camila Rocha"
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium text-slate-800"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                Registro CRMV / UF *
              </label>
              <input
                type="text"
                value={vetCrmv}
                onChange={(e) => setVetCrmv(e.target.value)}
                placeholder="Ex: CRMV-SP 42910"
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium text-slate-800"
                required
              />
            </div>
          </div>

          {/* Observações */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
              <FileText className="w-3.5 h-3.5 text-slate-400" />
              Observações / Reações
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ex: Aplicação subcutânea na região dorsal. Sem reações adversas imediatas."
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
              <span>{loading ? 'Registrando...' : 'Confirmar Aplicação'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Quick Creation Modals */}
      <NewVaccineCatalogModal
        isOpen={isNewVaccineOpen}
        onClose={() => setIsNewVaccineOpen(false)}
        onSuccess={handleVaccineCreated}
      />

      <NewVaccineBatchModal
        isOpen={isNewBatchOpen}
        defaultCatalogId={selectedCatalogId}
        onClose={() => setIsNewBatchOpen(false)}
        onSuccess={handleBatchCreated}
      />
    </div>
  );
};

