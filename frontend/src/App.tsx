import React, { useState, useEffect } from 'react';
import { Activity, Database, Bot, Bell } from 'lucide-react';
import { Header } from './components/Header';
import { StatusCard } from './components/StatusCard';
import { ChatWidget } from './components/ChatWidget';
import { AlertsWidget } from './components/AlertsWidget';
import { RoadmapGrid } from './components/RoadmapGrid';
import { fetchSystemStatus, SystemStatus } from './services/api';

export default function App() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

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
      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full space-y-8">
        {/* Banner de Boas-Vindas */}
        <div className="bg-gradient-to-r from-emerald-600 to-teal-700 rounded-2xl p-6 text-white shadow-md">
          <div className="max-w-3xl">
            <h2 className="text-2xl font-bold">SmartPetShop: Painel Inteligente & Atendimento IA 🚀</h2>
            <p className="mt-2 text-emerald-50 text-sm leading-relaxed">
              Sistema modular com FastAPI, PostgreSQL, Agentes Gemini com Function Calling e React totalmente componentizado.
            </p>
          </div>
        </div>

        {/* Status Grid com componentes reutilizáveis */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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
            value="Gemini 2.5 Flash"
            subtitle="Function Calling ativo"
            icon={Bot}
            bgColor="bg-purple-50"
            iconColor="text-purple-600"
          />
          <StatusCard
            title="Agente Alertas"
            value="Preditivo Ativo"
            subtitle="Vacinas e Retornos"
            icon={Bell}
            bgColor="bg-amber-50"
            iconColor="text-amber-600"
          />
        </div>

        {/* Seção Principal: Chatbot IA & Alertas Preditivos lado a lado */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          <div className="lg:col-span-7">
            <ChatWidget />
          </div>
          <div className="lg:col-span-5 h-[520px]">
            <AlertsWidget />
          </div>
        </div>

        {/* Componente Roadmap */}
        <RoadmapGrid />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-500 bg-white">
        SmartPetShop &bull; Arquitetura Componentizada &bull; 2026
      </footer>
    </div>
  );
}
