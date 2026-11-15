import React from 'react';
import { Dog, Building2, Shield } from 'lucide-react';

interface HeaderProps {
  isOnline: boolean;
  isLoading: boolean;
  companyName?: string;
  userRole?: string;
}

export const Header: React.FC<HeaderProps> = ({
  isOnline,
  isLoading,
  companyName = 'Pet Shop Patas & Pelos (Unidade A)',
  userRole = 'ADMIN'
}) => {
  return (
    <header className="bg-white border-b border-slate-200 px-6 py-3.5 sticky top-0 z-20 shadow-sm">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Logo & Marca */}
        <div className="flex items-center space-x-3">
          <div className="bg-emerald-600 text-white p-2.5 rounded-xl shadow-md flex items-center justify-center">
            <Dog className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800 tracking-tight">SmartPetShop</h1>
            <p className="text-xs text-slate-500 font-medium">SaaS Multi-empresa com Agentes de IA</p>
          </div>
        </div>

        {/* Multi-tenancy & Perfil Badges */}
        <div className="flex items-center flex-wrap gap-2.5">
          {/* Tenant Badge */}
          <div className="flex items-center space-x-1.5 bg-slate-100 border border-slate-200 px-3 py-1 rounded-xl text-xs font-semibold text-slate-700">
            <Building2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>{companyName}</span>
          </div>

          {/* User Role Badge */}
          <div className="flex items-center space-x-1.5 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-xl text-xs font-bold text-emerald-800 uppercase tracking-wider">
            <Shield className="w-3 h-3 text-emerald-600" />
            <span>{userRole}</span>
          </div>

          {/* Status Indicator */}
          <div className="flex items-center space-x-2 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-xl">
            <span className="flex h-2 w-2 relative">
              <span
                className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  !isOnline ? 'bg-red-400' : 'bg-emerald-400'
                }`}
              ></span>
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  !isOnline ? 'bg-red-500' : 'bg-emerald-500'
                }`}
              ></span>
            </span>
            <span className="text-[11px] font-semibold text-slate-600">
              {isLoading ? 'Conectando...' : isOnline ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
