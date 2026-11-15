import React, { useState } from 'react';
import { X, Syringe, Shield, Calendar, AlertCircle } from 'lucide-react';
import { createVaccineCatalog, VaccineCatalogItem } from '../services/api';

interface NewVaccineCatalogModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newCatalog: VaccineCatalogItem) => void;
}

export const NewVaccineCatalogModal: React.FC<NewVaccineCatalogModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState('');
  const [species, setSpecies] = useState('CANINO');
  const [type, setType] = useState<'OBRIGATORIA' | 'OPCIONAL'>('OBRIGATORIA');
  const [recommendedAgeWeeks, setRecommendedAgeWeeks] = useState(8);
  const [dosesRequired, setDosesRequired] = useState(3);
  const [boosterIntervalDays, setBoosterIntervalDays] = useState(365);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('O nome da vacina é obrigatório.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const created = await createVaccineCatalog({
        name: name.trim(),
        species,
        type,
        recommended_age_weeks: Number(recommendedAgeWeeks),
        doses_required: Number(dosesRequired),
        booster_interval_days: Number(boosterIntervalDays),
        description: description.trim() || undefined,
      });

      onSuccess(created);
      onClose();
      // Reset form
      setName('');
      setDescription('');
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Erro ao cadastrar vacina no catálogo.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center">
              <Syringe className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-800">Cadastrar Nova Vacina</h3>
              <p className="text-xs text-slate-500">Adicione um imunizante ao catálogo oficial</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-start space-x-2 text-xs text-red-700">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Nome da Vacina / Imunizante *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: V10 Vanguard Plus, Antirrábica Nobivac, GiardiaVax"
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 font-medium text-slate-800"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Espécie Indicada *
              </label>
              <select
                value={species}
                onChange={(e) => setSpecies(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 font-medium text-slate-800"
              >
                <option value="CANINO">Canino (Cães)</option>
                <option value="FELINO">Felino (Gatos)</option>
                <option value="AMBOS">Ambos (Cães e Gatos)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Classificação *
              </label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value as any)}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 font-medium text-slate-800"
              >
                <option value="OBRIGATORIA">Obrigatória / Essencial</option>
                <option value="OPCIONAL">Opcional / Recomendada</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Calendar className="w-3 h-3 text-emerald-600" />
                Idade Inicial
              </label>
              <div className="relative">
                <input
                  type="number"
                  min="0"
                  max="104"
                  value={recommendedAgeWeeks}
                  onChange={(e) => setRecommendedAgeWeeks(Number(e.target.value))}
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none text-slate-800"
                  required
                />
                <span className="absolute right-2.5 top-2.5 text-[10px] text-slate-400 font-bold">sem.</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Shield className="w-3 h-3 text-emerald-600" />
                Doses Primárias
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={dosesRequired}
                onChange={(e) => setDosesRequired(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none text-slate-800"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Calendar className="w-3 h-3 text-emerald-600" />
                Reforço
              </label>
              <div className="relative">
                <input
                  type="number"
                  min="1"
                  max="3650"
                  value={boosterIntervalDays}
                  onChange={(e) => setBoosterIntervalDays(Number(e.target.value))}
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none text-slate-800"
                  required
                />
                <span className="absolute right-2.5 top-2.5 text-[10px] text-slate-400 font-bold">dias</span>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Descrição e Indicações Clínicas (opcional)
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Ex: Protege contra Cinomose, Hepatite Infecciosa, Adenovírus, Parvovirose, Parainfluenza e Coronavirose canina."
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 text-slate-800 resize-none"
            />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
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
              className="px-4 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl transition-colors shadow-sm disabled:opacity-50 flex items-center space-x-1.5"
            >
              {loading ? <span>Cadastrando...</span> : <span>Salvar Vacina</span>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

