import React, { useState, useEffect } from 'react';
import {
  Syringe,
  FlaskConical,
  Sparkles,
  Plus,
  Search,
  CheckCircle,
  AlertTriangle,
  Clock,
  Building2,
  Layers,
  Filter,
  Loader2
} from 'lucide-react';
import {
  fetchVaccineCatalogs,
  fetchVaccineBatches,
  fetchServices,
  VaccineCatalogItem,
  VaccineBatchItem,
  ServiceItem
} from '../services/api';
import { NewVaccineCatalogModal } from './NewVaccineCatalogModal';
import { NewVaccineBatchModal } from './NewVaccineBatchModal';
import { NewServiceModal } from './NewServiceModal';

type CatalogTab = 'vaccines' | 'batches' | 'services';

export const CatalogManagementView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<CatalogTab>('vaccines');
  const [catalogs, setCatalogs] = useState<VaccineCatalogItem[]>([]);
  const [batches, setBatches] = useState<VaccineBatchItem[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [speciesFilter, setSpeciesFilter] = useState('ALL');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [message, setMessage] = useState<string | null>(null);

  // Modals state
  const [isVaccineModalOpen, setIsVaccineModalOpen] = useState(false);
  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false);
  const [isServiceModalOpen, setIsServiceModalOpen] = useState(false);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [catsData, batchesData, servsData] = await Promise.all([
        fetchVaccineCatalogs(),
        fetchVaccineBatches(undefined, false),
        fetchServices(undefined, false),
      ]);
      setCatalogs(catsData);
      setBatches(batchesData);
      setServices(servsData);
    } catch (err) {
      console.error('Erro ao carregar dados do catálogo:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleVaccineCreated = (newCat: VaccineCatalogItem) => {
    setCatalogs((prev) => [newCat, ...prev]);
    setMessage(`Vacina "${newCat.name}" cadastrada com sucesso no catálogo!`);
  };

  const handleBatchCreated = (newBatch: VaccineBatchItem) => {
    setBatches((prev) => [newBatch, ...prev]);
    setMessage(`Lote de ampola "${newBatch.batch_number}" cadastrado com sucesso!`);
  };

  const handleServiceCreated = (newServ: ServiceItem) => {
    setServices((prev) => [newServ, ...prev]);
    setMessage(`Item "${newServ.name}" cadastrado com sucesso em ${newServ.category}!`);
  };

  // Filtragens
  const filteredCatalogs = catalogs.filter((c) => {
    const matchesSearch = c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.description && c.description.toLowerCase().includes(search.toLowerCase()));
    const matchesSpecies = speciesFilter === 'ALL' || c.species === speciesFilter || c.species === 'AMBOS';
    return matchesSearch && matchesSpecies;
  });

  const filteredBatches = batches.filter((b) => {
    const matchesSearch =
      b.batch_number.toLowerCase().includes(search.toLowerCase()) ||
      b.manufacturer.toLowerCase().includes(search.toLowerCase()) ||
      (b.vaccine_catalog && b.vaccine_catalog.name.toLowerCase().includes(search.toLowerCase()));
    return matchesSearch;
  });

  const filteredServices = services.filter((s) => {
    const matchesSearch =
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.category.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = categoryFilter === 'ALL' || s.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const categories = Array.from(new Set(services.map((s) => s.category)));

  const getExpirationBadge = (expStr: string) => {
    const today = new Date();
    const exp = new Date(expStr);
    const diffDays = Math.ceil((exp.getTime() - today.getTime()) / (1000 * 3600 * 24));

    if (diffDays < 0) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-red-100 text-red-700">
          <AlertTriangle className="w-3 h-3 text-red-600" />
          Vencido ({exp.toLocaleDateString('pt-BR')})
        </span>
      );
    } else if (diffDays <= 30) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800">
          <Clock className="w-3 h-3 text-amber-600" />
          Vence em {diffDays}d ({exp.toLocaleDateString('pt-BR')})
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800">
          <CheckCircle className="w-3 h-3 text-emerald-600" />
          Válido até {exp.toLocaleDateString('pt-BR')}
        </span>
      );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Quick Action Buttons */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <Layers className="w-5 h-5 text-emerald-600" />
            Catálogo: Vacinas, Lotes de Ampolas & Serviços Adicionais
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Gerencie o catálogo sanitário oficial CFMV, controle de ampolas e a tabela de adicionais de atendimento
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setIsVaccineModalOpen(true)}
            className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white transition-colors shadow-2xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Nova Vacina</span>
          </button>

          <button
            onClick={() => setIsBatchModalOpen(true)}
            className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white transition-colors shadow-2xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Novo Lote Ampola</span>
          </button>

          <button
            onClick={() => setIsServiceModalOpen(true)}
            className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white transition-colors shadow-2xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Novo Adicional / Serviço</span>
          </button>
        </div>
      </div>

      {message && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center justify-between animate-fade-in">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="text-xs font-bold hover:text-emerald-900">
            &times;
          </button>
        </div>
      )}

      {/* Tabs Menu & Search */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                setActiveTab('vaccines');
                setSearch('');
              }}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'vaccines'
                  ? 'bg-emerald-600 text-white shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Syringe className="w-3.5 h-3.5" />
              <span>Vacinas do Catálogo ({catalogs.length})</span>
            </button>

            <button
              onClick={() => {
                setActiveTab('batches');
                setSearch('');
              }}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'batches'
                  ? 'bg-teal-600 text-white shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <FlaskConical className="w-3.5 h-3.5" />
              <span>Lotes de Ampolas ({batches.length})</span>
            </button>

            <button
              onClick={() => {
                setActiveTab('services');
                setSearch('');
              }}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'services'
                  ? 'bg-amber-600 text-white shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Serviços & Adicionais ({services.length})</span>
            </button>
          </div>

          {/* Quick Search */}
          <div className="relative min-w-[240px]">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por nome, lote ou fabricante..."
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
            />
          </div>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl">
            <Loader2 className="w-8 h-8 text-emerald-600 animate-spin mb-3" />
            <p className="text-sm font-semibold text-slate-600">Carregando catálogo e lotes...</p>
          </div>
        ) : (
          <>
            {/* Tab 1: Catálogo de Vacinas */}
            {activeTab === 'vaccines' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                  <Filter className="w-3 h-3 text-slate-400" />
                  Filtrar Espécie:
                </span>
                {['ALL', 'CANINO', 'FELINO', 'AMBOS'].map((sp) => (
                  <button
                    key={sp}
                    onClick={() => setSpeciesFilter(sp)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-colors ${
                      speciesFilter === sp
                        ? 'bg-slate-800 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {sp === 'ALL' ? 'Todas' : sp === 'CANINO' ? 'Caninos' : sp === 'FELINO' ? 'Felinos' : 'Ambos'}
                  </button>
                ))}
              </div>

              <span className="text-xs text-slate-400">
                Exibindo {filteredCatalogs.length} de {catalogs.length} vacinas
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredCatalogs.map((c) => (
                <div
                  key={c.id}
                  className="bg-slate-50/70 border border-slate-200 rounded-xl p-4 space-y-3 hover:border-emerald-300 transition-colors shadow-2xs"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-bold text-slate-800">{c.name}</h4>
                      <div className="flex items-center gap-1.5 mt-1">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-200 text-slate-700">
                          {c.species}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            c.type === 'OBRIGATORIA'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {c.type === 'OBRIGATORIA' ? 'Obrigatória' : 'Opcional / Recomendada'}
                        </span>
                      </div>
                    </div>
                    <div className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                      <Syringe className="w-3.5 h-3.5" />
                    </div>
                  </div>

                  {c.description && (
                    <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                      {c.description}
                    </p>
                  )}

                  <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-200/60 text-center">
                    <div className="bg-white rounded-lg p-1.5 border border-slate-200/70">
                      <p className="text-[10px] text-slate-400 font-bold uppercase">Idade Mín.</p>
                      <p className="text-xs font-bold text-slate-700">{c.recommended_age_weeks} sem.</p>
                    </div>
                    <div className="bg-white rounded-lg p-1.5 border border-slate-200/70">
                      <p className="text-[10px] text-slate-400 font-bold uppercase">Doses</p>
                      <p className="text-xs font-bold text-slate-700">{c.doses_required} dose(s)</p>
                    </div>
                    <div className="bg-white rounded-lg p-1.5 border border-slate-200/70">
                      <p className="text-[10px] text-slate-400 font-bold uppercase">Reforço</p>
                      <p className="text-xs font-bold text-slate-700">
                        {c.booster_interval_days === 365 ? 'Anual' : `${c.booster_interval_days}d`}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {filteredCatalogs.length === 0 && (
              <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
                <Syringe className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-xs font-semibold text-slate-600">Nenhuma vacina encontrada.</p>
                <button
                  onClick={() => setIsVaccineModalOpen(true)}
                  className="mt-2 text-xs font-bold text-emerald-600 hover:underline"
                >
                  Clique para cadastrar uma nova vacina
                </button>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Lotes de Ampolas */}
        {activeTab === 'batches' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Lotes e Ampolas de Imunizantes ({filteredBatches.length})
              </span>
              <button
                onClick={() => setIsBatchModalOpen(true)}
                className="text-xs font-bold text-teal-600 hover:text-teal-700 flex items-center gap-1 hover:underline"
              >
                <Plus className="w-3 h-3" />
                <span>Adicionar Lote Ampola</span>
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 text-[11px] font-bold text-slate-400 uppercase tracking-wider bg-slate-50/50">
                    <th className="py-2.5 px-3">Lote / Ampola</th>
                    <th className="py-2.5 px-3">Vacina Vinculada</th>
                    <th className="py-2.5 px-3">Fabricante / Laboratório</th>
                    <th className="py-2.5 px-3">Data de Validade</th>
                    <th className="py-2.5 px-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                  {filteredBatches.map((b) => (
                    <tr key={b.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-3 font-bold font-mono text-teal-700">
                        {b.batch_number}
                      </td>
                      <td className="py-3 px-3">
                        <span className="font-semibold text-slate-800">
                          {b.vaccine_catalog ? b.vaccine_catalog.name : 'Vacina vinculada'}
                        </span>
                        {b.vaccine_catalog && (
                          <span className="text-[10px] text-slate-400 ml-1.5">
                            ({b.vaccine_catalog.species})
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-slate-600 flex items-center gap-1">
                        <Building2 className="w-3 h-3 text-slate-400" />
                        <span>{b.manufacturer}</span>
                      </td>
                      <td className="py-3 px-3">
                        {getExpirationBadge(b.expiration_date)}
                      </td>
                      <td className="py-3 px-3 text-right">
                        {b.active ? (
                          <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold bg-teal-100 text-teal-800">
                            Ativo
                          </span>
                        ) : (
                          <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-500">
                            Inativo
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {filteredBatches.length === 0 && (
              <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
                <FlaskConical className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-xs font-semibold text-slate-600">Nenhum lote de ampola cadastrado.</p>
                <button
                  onClick={() => setIsBatchModalOpen(true)}
                  className="mt-2 text-xs font-bold text-teal-600 hover:underline"
                >
                  Clique para cadastrar a primeira ampola/lote
                </button>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Serviços & Adicionais */}
        {activeTab === 'services' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                  <Filter className="w-3 h-3 text-slate-400" />
                  Categoria:
                </span>
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="px-2.5 py-1 text-xs font-semibold bg-slate-100 border border-slate-200 rounded-lg focus:outline-none text-slate-700"
                >
                  <option value="ALL">Todas as Categorias</option>
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={() => setIsServiceModalOpen(true)}
                className="text-xs font-bold text-amber-600 hover:text-amber-700 flex items-center gap-1 hover:underline"
              >
                <Plus className="w-3 h-3" />
                <span>Novo Adicional / Serviço</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredServices.map((s) => (
                <div
                  key={s.id}
                  className="bg-white border border-slate-200 rounded-xl p-4 space-y-3 hover:border-amber-300 transition-colors shadow-2xs"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-bold text-slate-800">{s.name}</h4>
                      <span className="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                        {s.category}
                      </span>
                    </div>
                    <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
                      <Sparkles className="w-3.5 h-3.5" />
                    </div>
                  </div>

                  {s.description && (
                    <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                      {s.description}
                    </p>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                    <span className="font-bold text-base text-slate-800">
                      R$ {Number(s.price).toFixed(2).replace('.', ',')}
                    </span>
                    <span className="text-slate-400 flex items-center gap-1 text-[11px]">
                      <Clock className="w-3 h-3 text-slate-400" />
                      {s.duration_minutes} min
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {filteredServices.length === 0 && (
              <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
                <Sparkles className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-xs font-semibold text-slate-600">Nenhum adicional ou serviço encontrado.</p>
                <button
                  onClick={() => setIsServiceModalOpen(true)}
                  className="mt-2 text-xs font-bold text-amber-600 hover:underline"
                >
                  Clique para cadastrar um novo serviço ou adicional
                </button>
              </div>
            )}
          </div>
        )}
        </>
        )}
      </div>

      {/* Modais de Cadastro */}
      <NewVaccineCatalogModal
        isOpen={isVaccineModalOpen}
        onClose={() => setIsVaccineModalOpen(false)}
        onSuccess={handleVaccineCreated}
      />

      <NewVaccineBatchModal
        isOpen={isBatchModalOpen}
        onClose={() => setIsBatchModalOpen(false)}
        onSuccess={handleBatchCreated}
      />

      <NewServiceModal
        isOpen={isServiceModalOpen}
        onClose={() => setIsServiceModalOpen(false)}
        onSuccess={handleServiceCreated}
      />
    </div>
  );
};
