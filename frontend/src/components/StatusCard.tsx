import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatusCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: LucideIcon;
  bgColor: string;
  iconColor: string;
}

export const StatusCard: React.FC<StatusCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  bgColor,
  iconColor,
}) => {
  return (
    <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-start space-x-4 hover:shadow-md transition-shadow">
      <div className={`p-3 rounded-xl ${bgColor} ${iconColor}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">{title}</p>
        <h3 className="text-lg font-bold text-slate-800 mt-1 truncate">{value}</h3>
        <p className="text-xs text-slate-500 mt-0.5 truncate">{subtitle}</p>
      </div>
    </div>
  );
};

