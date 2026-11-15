import React from 'react';
import { Dog } from 'lucide-react';

interface HeaderProps {
  isOnline: boolean;
  isLoading: boolean;
}

export const Header: React.FC<HeaderProps> = ({ isOnline, isLoading }) => {
  return (
    <header className="bg-white border-b border-slate-200 px-6 py-4 sticky top-0 z-20 shadow-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-emerald-600 text-white p-2.5 rounded-xl shadow-md flex items-center justify-center">
            <Dog className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800 tracking-tight">SmartPetShop</h1>
            <p className="text-xs text-slate-500 font-medium">Sistema Inteligente com Agentes de IA</p>
          </div>
        </div>

        <div className="flex items-center space-x-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-full">
          <span className="flex h-2.5 w-2.5 relative">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                !isOnline ? 'bg-red-400' : 'bg-emerald-400'
              }`}
            ></span>
            <span
              className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                !isOnline ? 'bg-red-500' : 'bg-emerald-500'
              }`}
            ></span>
          </span>
          <span className="text-xs font-semibold text-slate-700">
            {isLoading ? 'Verificando...' : isOnline ? 'FastAPI Online' : 'API Offline'}
          </span>
        </div>
      </div>
    </header>
  );
};
