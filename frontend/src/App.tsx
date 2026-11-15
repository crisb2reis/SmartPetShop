import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Dog, Activity, Bot, Bell, Calendar, Database, CheckCircle2, AlertCircle } from 'lucide-react'

interface BackendStatus {
  system?: string
  version?: string
  status?: string
}

export default function App() {
  const [backendStatus, setBackendStatus] = useState<BackendStatus | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get('http://localhost:8000/')
        setBackendStatus(response.data)
        setError(null)
      } catch (err: any) {
        setError(err.message || 'Erro ao conectar à API FastAPI')
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()
  }, [])

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-emerald-600 text-white p-2.5 rounded-xl shadow-sm">
              <Dog className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800">SmartPetShop</h1>
              <p className="text-xs text-slate-500">Sistema Inteligente com Agentes de IA</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="flex h-2.5 w-2.5 relative">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${error ? 'bg-red-400' : 'bg-emerald-400'}`}></span>
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${error ? 'bg-red-500' : 'bg-emerald-500'}`}></span>
            </span>
            <span className="text-xs font-medium text-slate-600">
              {loading ? 'Checando API...' : error ? 'API Offline (Inicie o Backend)' : 'FastAPI Online'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full space-y-8">
        {/* Welcome Banner */}
        <div className="bg-gradient-to-r from-emerald-600 to-teal-700 rounded-2xl p-6 text-white shadow-md">
          <div className="max-w-3xl">
            <h2 className="text-2xl font-bold">Ambiente SmartPetShop Inicializado com Sucesso! 🚀</h2>
            <p className="mt-2 text-emerald-50 text-sm leading-relaxed">
              Estrutura base orquestrada via Docker Compose com FastAPI, PostgreSQL, React e Agentes Inteligentes prontos para desenvolvimento.
            </p>
          </div>
        </div>

        {/* Status Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-start space-x-4">
            <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">FastAPI Backend</p>
              <h3 className="text-lg font-bold text-slate-800 mt-1">
                {error ? 'Aguardando' : (backendStatus?.version ? `v${backendStatus.version}` : 'Porta 8000')}
              </h3>
              <p className="text-xs text-slate-500 mt-1">Swagger: /api/v1/docs</p>
            </div>
          </div>

          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-start space-x-4">
            <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">PostgreSQL</p>
              <h3 className="text-lg font-bold text-slate-800 mt-1">Porta 5432</h3>
              <p className="text-xs text-slate-500 mt-1">smartpetshop DB</p>
            </div>
          </div>

          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-start space-x-4">
            <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Agente Chatbot</p>
              <h3 className="text-lg font-bold text-slate-800 mt-1">Gemini AI</h3>
              <p className="text-xs text-slate-500 mt-1">Function Calling</p>
            </div>
          </div>

          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-start space-x-4">
            <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Agente Alertas</p>
              <h3 className="text-lg font-bold text-slate-800 mt-1">Preditivo</h3>
              <p className="text-xs text-slate-500 mt-1">Vacinas e Banho</p>
            </div>
          </div>
        </div>

        {/* Modules Roadmap */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-emerald-600" />
            Módulos em Desenvolvimento
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { title: 'Docker Compose & Infra', status: 'Em Andamento', icon: CheckCircle2, color: 'text-emerald-600' },
              { title: 'Modelos e Migrations (PostgreSQL)', status: 'Próximo', icon: Database, color: 'text-slate-400' },
              { title: 'CRUD de Pets e Tutores', status: 'Backlog', icon: Dog, color: 'text-slate-400' },
              { title: 'Agenda de Banho, Tosa e Consultas', status: 'Backlog', icon: Calendar, color: 'text-slate-400' },
              { title: 'Atendimento Conversacional (Gemini)', status: 'Backlog', icon: Bot, color: 'text-slate-400' },
              { title: 'Notificações Preditivas e Retorno', status: 'Backlog', icon: Bell, color: 'text-slate-400' },
            ].map((module, i) => {
              const Icon = module.icon
              return (
                <div key={i} className="flex items-center justify-between p-4 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="flex items-center space-x-3">
                    <Icon className={`w-5 h-5 ${module.color}`} />
                    <span className="text-sm font-medium text-slate-700">{module.title}</span>
                  </div>
                  <span className="text-xs px-2.5 py-1 rounded-full font-medium bg-white text-slate-600 border border-slate-200">
                    {module.status}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-500 bg-white">
        SmartPetShop &bull; Desenvolvido com Antigravity &bull; 2026
      </footer>
    </div>
  )
}
