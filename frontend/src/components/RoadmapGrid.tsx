import React from 'react';
import { Calendar, Database, Dog, Bot, Bell, CheckCircle2, ShieldCheck, LayoutDashboard } from 'lucide-react';

interface ModuleItem {
  title: string;
  status: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  isCompleted?: boolean;
}

export const RoadmapGrid: React.FC = () => {
  const modules: ModuleItem[] = [
    { title: 'Docker Compose & Infra', status: 'Concluído', icon: CheckCircle2, color: 'text-emerald-600', isCompleted: true },
    { title: 'Modelos e Migrations (PostgreSQL)', status: 'Concluído', icon: Database, color: 'text-emerald-600', isCompleted: true },
    { title: 'CRUD de Pets e Tutores', status: 'Concluído', icon: Dog, color: 'text-emerald-600', isCompleted: true },
    { title: 'Agenda de Banho, Tosa e Consultas', status: 'Concluído', icon: Calendar, color: 'text-emerald-600', isCompleted: true },
    { title: 'Atendimento Conversacional (Gemini)', status: 'Concluído', icon: Bot, color: 'text-emerald-600', isCompleted: true },
    { title: 'Notificações Preditivas e Retorno', status: 'Concluído', icon: Bell, color: 'text-emerald-600', isCompleted: true },
    { title: 'Setup do Frontend React & Tailwind', status: 'Concluído', icon: LayoutDashboard, color: 'text-emerald-600', isCompleted: true },
    { title: 'Dashboard de Agendamentos e Alertas', status: 'Próximo', icon: Calendar, color: 'text-amber-500' },
    { title: 'Segurança & Hardening (OWASP/SAST)', status: 'Backlog', icon: ShieldCheck, color: 'text-slate-400' },
  ];

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
      <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
        <Calendar className="w-5 h-5 text-emerald-600" />
        Módulos do Sistema
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {modules.map((m, i) => {
          const Icon = m.icon;
          return (
            <div
              key={i}
              className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-100"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <Icon className={`w-4 h-4 flex-shrink-0 ${m.color}`} />
                <span className="text-xs font-semibold text-slate-700 truncate">{m.title}</span>
              </div>
              <span
                className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider flex-shrink-0 ${
                  m.isCompleted
                    ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                    : m.status === 'Próximo'
                    ? 'bg-amber-100 text-amber-700 border border-amber-200'
                    : 'bg-white text-slate-500 border border-slate-200'
                }`}
              >
                {m.status}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
