import React, { useState, useEffect } from 'react';
import {
  X,
  Syringe,
  Calendar,
  ShieldCheck,
  AlertTriangle,
  Clock,
  User,
  Plus,
  FileBadge,
  Printer,
  ChevronRight,
  Info
} from 'lucide-react';
import {
  fetchPetVaccinationCard,
  VaccineCardData,
  VaccineRecordItem,
  Pet
} from '../services/api';

interface VaccinationCardModalProps {
  isOpen: boolean;
  pet: Pet | null;
  onClose: () => void;
  onOpenAddVaccine?: (pet: Pet) => void;
}

export const VaccinationCardModal: React.FC<VaccinationCardModalProps> = ({
  isOpen,
  pet,
  onClose,
  onOpenAddVaccine,
}) => {
  const [cardData, setCardData] = useState<VaccineCardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeSubTab, setActiveSubTab] = useState<'applied' | 'upcoming' | 'all'>('applied');

  const loadCard = async () => {
    if (!pet) return;
    setLoading(true);
    try {
      const data = await fetchPetVaccinationCard(pet.id);
      setCardData(data);
    } catch (err) {
      console.error('Erro ao carregar carteirinha de vacinação:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && pet) {
      loadCard();
    }
  }, [isOpen, pet]);

  if (!isOpen || !pet) return null;

  const getStatusBadge = (record: VaccineRecordItem) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    let isOverdue = false;
    let isDueSoon = false;
    let daysRemaining = 0;

    if (record.next_due_date) {
      const dueDate = new Date(record.next_due_date);
      dueDate.setHours(0, 0, 0, 0);
      const diffTime = dueDate.getTime() - today.getTime();
      daysRemaining = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

      if (daysRemaining < 0) {
        isOverdue = true;
      } else if (daysRemaining <= 30) {
        isDueSoon = true;
      }
    }

    if (record.status === 'ATRASADA' || isOverdue) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-200">
          <AlertTriangle className="w-3 h-3 text-red-600" />
          Atrasada {daysRemaining < 0 ? `(${Math.abs(daysRemaining)}d)` : ''}
        </span>
      );
    }

    if (isDueSoon) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200 animate-pulse">
          <Clock className="w-3 h-3 text-amber-600" />
          Vence em {daysRemaining}d
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
        <ShieldCheck className="w-3 h-3 text-emerald-600" />
        Em dia
      </span>
    );
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'Não definida';
    const [year, month, day] = dateStr.split('T')[0].split('-');
    return `${day}/${month}/${year}`;
  };

  const recordsToDisplay = () => {
    if (!cardData) return [];
    if (activeSubTab === 'applied') return cardData.applied_records;
    if (activeSubTab === 'upcoming') return cardData.upcoming_records;
    return cardData.all_records;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-3xl w-full max-h-[92vh] flex flex-col overflow-hidden">
        {/* Header estilo Caderneta Oficial */}
        <div className="bg-gradient-to-r from-emerald-700 via-emerald-600 to-teal-700 text-white px-6 py-5 flex items-start justify-between relative shadow-md">
          <div className="flex items-start space-x-3.5">
            <div className="w-12 h-12 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center shrink-0 shadow-inner">
              <Syringe className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
                  Carteirinha de Vacinação Digital
                </h2>
                <span className="bg-emerald-950/40 text-emerald-200 text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border border-emerald-400/30 flex items-center gap-1">
                  <FileBadge className="w-3 h-3" />
                  Padrão CFMV
                </span>
              </div>
              <p className="text-xs text-emerald-100 mt-1 flex items-center gap-2">
                <span>Paciente: <strong className="text-white font-bold">{pet.name}</strong> ({pet.breed || pet.species})</span>
                <span>&bull;</span>
                <span>Espécie: <strong className="text-white font-bold">{pet.species}</strong></span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => window.print()}
              title="Imprimir Carteirinha"
              className="p-2 text-white/80 hover:text-white hover:bg-white/10 rounded-xl transition-colors"
            >
              <Printer className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-white/80 hover:text-white hover:bg-white/10 rounded-xl transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Resumo de Doses & Ações Rápidas */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            {/* Contadores */}
            <div className="flex items-center space-x-2 text-xs">
              <div className="bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl font-semibold text-emerald-800 flex items-center gap-1.5 shadow-2xs">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>{cardData?.total_applied ?? 0} Aplicadas</span>
              </div>
              <div className="bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-xl font-semibold text-amber-800 flex items-center gap-1.5 shadow-2xs">
                <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                <span>{cardData?.due_soon_count ?? 0} A Vencer</span>
              </div>
              <div className="bg-red-50 border border-red-200 px-3 py-1.5 rounded-xl font-semibold text-red-800 flex items-center gap-1.5 shadow-2xs">
                <span className="w-2 h-2 rounded-full bg-red-500"></span>
                <span>{cardData?.overdue_count ?? 0} Atrasadas</span>
              </div>
            </div>
          </div>

          {onOpenAddVaccine && (
            <button
              onClick={() => onOpenAddVaccine(pet)}
              className="flex items-center space-x-1.5 text-xs font-bold px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Registrar Aplicação</span>
            </button>
          )}
        </div>

        {/* Subtabs de Navegação */}
        <div className="px-6 pt-3 border-b border-slate-200 flex space-x-2 bg-white">
          <button
            onClick={() => setActiveSubTab('applied')}
            className={`pb-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-1.5 ${
              activeSubTab === 'applied'
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>Doses Aplicadas (Histórico)</span>
            <span className="bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded-full text-[10px]">
              {cardData?.applied_records.length ?? 0}
            </span>
          </button>

          <button
            onClick={() => setActiveSubTab('upcoming')}
            className={`pb-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-1.5 ${
              activeSubTab === 'upcoming'
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>Próximas Doses / Alertas</span>
            <span className="bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded-full text-[10px]">
              {cardData?.upcoming_records.length ?? 0}
            </span>
          </button>

          <button
            onClick={() => setActiveSubTab('all')}
            className={`pb-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-1.5 ${
              activeSubTab === 'all'
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>Todas as Vacinas</span>
            <span className="bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded-full text-[10px]">
              {cardData?.all_records.length ?? 0}
            </span>
          </button>
        </div>

        {/* Lista de Vacinas */}
        <div className="p-6 overflow-y-auto space-y-3.5 flex-1 bg-slate-50/50">
          {loading ? (
            <div className="py-12 text-center text-xs text-slate-400">
              Carregando carteirinha de vacinação...
            </div>
          ) : recordsToDisplay().length === 0 ? (
            <div className="py-12 text-center bg-white rounded-2xl border border-slate-200 p-8 space-y-2">
              <Syringe className="w-8 h-8 text-slate-300 mx-auto" />
              <p className="text-sm font-semibold text-slate-700">Nenhum registro encontrado nesta seção.</p>
              <p className="text-xs text-slate-400">
                {activeSubTab === 'upcoming'
                  ? 'O pet não possui doses com vencimento próximo ou em atraso.'
                  : 'Clique em "Registrar Aplicação" para lançar a primeira dose com lote e CRMV.'}
              </p>
            </div>
          ) : (
            recordsToDisplay().map((record) => (
              <div
                key={record.id}
                className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-all space-y-3"
              >
                {/* Linha superior: Nome da Vacina + Status */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-100 flex items-center justify-center shrink-0 mt-0.5">
                      <Syringe className="w-5 h-5 text-emerald-600" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="text-sm font-bold text-slate-800">
                          {record.vaccine_catalog?.name || 'Vacina'}
                        </h4>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 uppercase">
                          {record.vaccine_catalog?.type || 'OBRIGATÓRIA'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {record.vaccine_catalog?.description || 'Imunização preventiva oficial para animais de estimação.'}
                      </p>
                    </div>
                  </div>

                  <div className="shrink-0">
                    {getStatusBadge(record)}
                  </div>
                </div>

                {/* Grid de Detalhes Regulamentares (CFMV) */}
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5 pt-3 border-t border-slate-100 text-xs bg-slate-50/70 p-3 rounded-xl">
                  {/* Data Aplicação */}
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Data da Aplicação</span>
                    <span className="font-semibold text-slate-700 flex items-center gap-1 mt-0.5">
                      <Calendar className="w-3 h-3 text-emerald-600" />
                      {formatDate(record.application_date)}
                    </span>
                  </div>

                  {/* Próximo Reforço */}
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Próximo Reforço</span>
                    <span className="font-semibold text-slate-700 flex items-center gap-1 mt-0.5">
                      <Clock className="w-3 h-3 text-amber-600" />
                      {formatDate(record.next_due_date)}
                    </span>
                  </div>

                  {/* Lote & Fabricante */}
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Lote / Fabricante</span>
                    <span className="font-semibold text-slate-700 truncate block mt-0.5" title={record.vaccine_batch?.manufacturer}>
                      {record.vaccine_batch?.batch_number || 'Lote Padrão'}
                      <span className="text-[10px] text-slate-400 font-normal block truncate">
                        {record.vaccine_batch?.manufacturer || 'Fabricante não inf.'}
                      </span>
                    </span>
                  </div>

                  {/* Médico Veterinário & CRMV */}
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Médico Veterinário</span>
                    <span className="font-semibold text-slate-700 truncate block mt-0.5" title={record.vet_name}>
                      {record.vet_name}
                      <span className="text-[10px] text-emerald-600 font-bold block">
                        {record.vet_crmv}
                      </span>
                    </span>
                  </div>
                </div>

                {/* Observações / Cuidados */}
                {record.notes && (
                  <div className="text-[11px] text-slate-600 bg-emerald-50/50 border border-emerald-100/60 p-2 rounded-lg flex items-start gap-1.5">
                    <Info className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <span><strong>Obs:</strong> {record.notes}</span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Footer Informativo de Normas Sanitárias */}
        <div className="px-6 py-3 bg-white border-t border-slate-200 flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center gap-1 text-[11px]">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            Certificado emitido em conformidade com as diretrizes do CFMV e controle de zoonoses.
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-xl transition-colors"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
};
