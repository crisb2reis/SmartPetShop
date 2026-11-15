import React, { useState, useEffect } from 'react';
import {
  Activity,
  Database,
  Bot,
  Bell,
  Calendar,
  Users,
  MessageSquare
} from 'lucide-react';
import { Header } from './components/Header';
import { StatusCard } from './components/StatusCard';
import { AppointmentsDashboard } from './components/AppointmentsDashboard';
import { ChatWidget } from './components/ChatWidget';
import { AlertsWidget } from './components/AlertsWidget';
import { TutorsPetsView } from './components/TutorsPetsView';
import { RoadmapGrid } from './components/RoadmapGrid';
import { fetchSystemStatus, SystemStatus } from './services/api';

type TabType = 'agenda' | 'ia' | 'cadastros';

export default function App() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('agenda');

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const data = await fetchSystemStatus();
        setSystemStatus(data);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Falha na conexão com a API');
      } finally {
        setLoading(false);
      }
    };

    loadStatus();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Componente Header */}
      <Header isOnline={!error && !loading} isLoading={loading} />

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-6 flex-1 w-full space-y-6">
        {/* Metric Cards Top */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatusCard
            title="FastAPI Backend"
            value={systemStatus?.version ? `v${systemStatus.version}` : 'Porta 8000'}
            subtitle="Swagger: /api/v1/docs"
            icon={Activity}
            bgColor="bg-blue-50"
            iconColor="text-blue-600"
          />
          <StatusCard
            title="PostgreSQL"
            value="Porta 5432"
            subtitle="smartpetshop DB"
            icon={Database}
            bgColor="bg-indigo-50"
            iconColor="text-indigo-600"
          />
          <StatusCard
            title="Agente Chatbot"
            value="Rex (Gemini)"
            subtitle="Atendimento & Function Calling"
            icon={Bot}
            bgColor="bg-purple-50"
            iconColor="text-purple-600"
          />
          <StatusCard
            title="Agente Alertas"
            value="Preditivo Ativo"
            subtitle="Vacinas e Retorno de Banho"
            icon={Bell}
            bgColor="bg-amber-50"
            iconColor="text-amber-600"
          />
        </div>

        {/* Tab Navigation Menu */}
        <div className="flex items-center space-x-2 border-b border-slate-200 pb-2">
          <button
            onClick={() => setActiveTab('agenda')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-bold transition-all ${
              activeTab === 'agenda'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Calendar className="w-4 h-4" />
            <span>Recepção & Grade de Atendimentos</span>
          </button>

          <button
            onClick={() => setActiveTab('ia')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-bold transition-all ${
              activeTab === 'ia'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span>Atendimento IA & Alertas</span>
          </button>

          <button
            onClick={() => setActiveTab('cadastros')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-bold transition-all ${
              activeTab === 'cadastros'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Tutores & Pets</span>
          </button>
        </div>

        {/* Tab Contents */}
        {activeTab === 'agenda' && <AppointmentsDashboard />}

        {activeTab === 'ia' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-7">
              <ChatWidget />
            </div>
            <div className="lg:col-span-5 h-[520px]">
              <AlertsWidget />
            </div>
          </div>
        )}

        {activeTab === 'cadastros' && <TutorsPetsView />}

        {/* Roadmap de Módulos */}
        <RoadmapGrid />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-500 bg-white">
        SmartPetShop &bull; Recepção & Atendimento Inteligente &bull; 2026
      </footer>
    </div>
  );
}
