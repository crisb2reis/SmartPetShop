import React, { useState, useEffect } from 'react';
import { X, FlaskConical, Calendar, Building2, Tag, AlertCircle } from 'lucide-react';
import { createVaccineBatch, fetchVaccineCatalogs, VaccineBatchItem, VaccineCatalogItem } from '../services/api';

interface NewVaccineBatchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newBatch: VaccineBatchItem) => void;
  defaultCatalogId?: string;
}

export const NewVaccineBatchModal: React.FC<NewVaccineBatchModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  defaultCatalogId,
}) => {
  const [catalogs, setCatalogs] = useState<VaccineCatalogItem[]>([]);
  const [selectedCatalogId, setSelectedCatalogId] = useState('');
  const [batchNumber, setBatchNumber] = useState('');
  const [manufacturer, setManufacturer] = useState('');
  const [expirationDate, setExpirationDate] = useState('');
  const [active, setActive] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchVaccineCatalogs()
        .then((data) => {
          setCatalogs(data);
          if (defaultCatalogId) {
            setSelectedCatalogId(defaultCatalogId);
          } else if (data.length > 0 && !selectedCatalogId) {
            setSelectedCatalogId(data[0].id);
          }
        })
        .catch((err) => console.error('Erro ao carregar catálogo de vacinas:', err));

      // Data de validade padrão: 1 ano à frente
      const nextYear = new Date();
      nextYear.setFullYear(nextYear.getFullYear() + 1);
      setExpirationDate(nextYear.toISOString().split('T')[0]);
    }
  }, [isOpen, defaultCatalogId]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCatalogId || !batchNumber.trim() || !manufacturer.trim() || !expirationDate) {
      setError('Por favor preencha todos os campos obrigatórios.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const created = await createVaccineBatch({
        vaccine_catalog_id: selectedCatalogId,
        batch_number: batchNumber.trim(),
        manufacturer: manufacturer.trim(),
        expiration_date: expirationDate,
        active,
      });

      onSuccess(created);
      onClose();
      // Reset
      setBatchNumber('');
      setManufacturer('');
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Erro ao cadastrar lote de ampola.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-md w-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center">
              <FlaskConical className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-800">Cadastrar Lote de Ampola</h3>
              <p className="text-xs text-slate-500">Rastreabilidade sanitária e controle de estoque</p>
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
              Vacina do Catálogo *
            </label>
            <select
              value={selectedCatalogId}
              onChange={(e) => setSelectedCatalogId(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-medium text-slate-800"
              required
            >
              {catalogs.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.species} - {c.type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
              <Tag className="w-3.5 h-3.5 text-teal-600" />
              Número do Lote / Ampola *
            </label>
            <input
              type="text"
              value={batchNumber}
              onChange={(e) => setBatchNumber(e.target.value)}
              placeholder="Ex: AMP-2026-X89, LOTE-998811"
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-medium text-slate-800"
              required
            />
            <p className="text-[11px] text-slate-400 mt-1">Impresso no frasco/ampola do imunizante.</p>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
              <Building2 className="w-3.5 h-3.5 text-teal-600" />
              Laboratório Fabricante *
            </label>
            <input
              type="text"
              value={manufacturer}
              onChange={(e) => setManufacturer(e.target.value)}
              placeholder="Ex: Zoetis, MSD Saúde Animal, Boehringer Ingelheim, Virbac"
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-medium text-slate-800"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-teal-600" />
              Data de Validade da Ampola *
            </label>
            <input
              type="date"
              value={expirationDate}
              onChange={(e) => setExpirationDate(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-medium text-slate-800"
              required
            />
          </div>

          <div className="flex items-center space-x-2 pt-1">
            <input
              type="checkbox"
              id="batch-active"
              checked={active}
              onChange={(e) => setActive(e.target.checked)}
              className="w-4 h-4 text-teal-600 rounded border-slate-300 focus:ring-teal-500"
            />
            <label htmlFor="batch-active" className="text-xs font-semibold text-slate-700 cursor-pointer">
              Lote ativo disponível para aplicação no consultório
            </label>
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
              className="px-4 py-2 text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 rounded-xl transition-colors shadow-sm disabled:opacity-50 flex items-center space-x-1.5"
            >
              {loading ? <span>Salvando...</span> : <span>Salvar Lote Ampola</span>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
