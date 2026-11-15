import React, { useState, useEffect } from 'react';
import { Bell, RefreshCw, CheckCircle2, AlertTriangle, Sparkles, X } from 'lucide-react';
import { fetchAlerts, runAlertScan, updateAlertStatus, AlertItem } from '../services/api';

export const AlertsWidget: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [scanning, setScanning] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const data = await fetchAlerts('pending');
      setAlerts(data);
    } catch (err) {
      console.error('Erro ao carregar alertas:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleScan = async () => {
    setScanning(true);
    setMessage(null);
    try {
      const result = await runAlertScan();
      setMessage(`Varredura concluída! ${result.total_pets_analyzed} pets analisados, ${result.alerts_generated} novos alertas.`);
      await loadAlerts();
    } catch (err) {
      setMessage('Erro ao executar varredura de alertas.');
    } finally {
      setScanning(false);
    }
  };

  const handleDismiss = async (id: string) => {
    try {
      await updateAlertStatus(id, 'dismissed');
      setAlerts((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      console.error('Erro ao dispensar alerta:', err);
    }
  };

  const getBadge = (type: string) => {
    if (type.includes('vaccine')) {
      return { text: 'Vacina a Vencer', bg: 'bg-red-50 text-red-700 border-red-200' };
    }
    if (type.includes('bath')) {
      return { text: 'Retorno Banho/Tosa', bg: 'bg-blue-50 text-blue-700 border-blue-200' };
    }
    return { text: 'Alerta Preventivo', bg: 'bg-amber-50 text-amber-700 border-amber-200' };
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col h-full">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-amber-50 text-amber-600 rounded-xl">
            <Bell className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-800 text-base flex items-center gap-1.5">
              Alertas Preditivos
              <Sparkles className="w-4 h-4 text-amber-500" />
            </h3>
            <p className="text-xs text-slate-500">Notificações automáticas de vacinas e banhos</p>
          </div>
        </div>

        <button
          onClick={handleScan}
          disabled={scanning}
          className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors disabled:opacity-50"
          title="Executar varredura preditiva com IA"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${scanning ? 'animate-spin text-emerald-600' : ''}`} />
          <span>{scanning ? 'Analisando...' : 'Rodar Varredura IA'}</span>
        </button>
      </div>

      {message && (
        <div className="mt-3 p-2.5 rounded-lg bg-emerald-50 text-emerald-800 text-xs font-medium border border-emerald-100 flex items-center justify-between">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="text-emerald-600 hover:text-emerald-900">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Lista de Alertas */}
      <div className="mt-4 flex-1 space-y-3 overflow-y-auto max-h-[360px] pr-1">
        {loading ? (
          <p className="text-xs text-slate-400 text-center py-8">Carregando alertas...</p>
        ) : alerts.length === 0 ? (
          <div className="text-center py-8 px-4 bg-slate-50 rounded-xl border border-slate-100">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
            <p className="text-xs font-semibold text-slate-700">Tudo em dia!</p>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Nenhuma vacina pendente ou pet sem visita recente no momento.
            </p>
          </div>
        ) : (
          alerts.map((alert) => {
            const badge = getBadge(alert.alert_type);
            return (
              <div
                key={alert.id}
                className="p-3.5 rounded-xl border border-slate-100 bg-slate-50/60 hover:bg-slate-50 transition-colors space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-slate-800">
                      {alert.pet?.name || 'Pet'}
                    </span>
                    <span className="text-[10px] text-slate-400">&bull;</span>
                    <span className="text-[11px] text-slate-500">
                      Tutor: {alert.tutor?.name || 'Tutor'}
                    </span>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${badge.bg}`}>
                    {badge.text}
                  </span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{alert.message}</p>
                <div className="flex items-center justify-end space-x-2 pt-1 border-t border-slate-100">
                  <button
                    onClick={() => handleDismiss(alert.id)}
                    className="text-[11px] font-medium text-slate-400 hover:text-slate-600 px-2 py-0.5 rounded"
                  >
                    Dispensar
                  </button>
                  <button
                    onClick={() => handleDismiss(alert.id)}
                    className="text-[11px] font-semibold text-emerald-600 hover:text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-md border border-emerald-100"
                  >
                    Marcar como Notificado
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

