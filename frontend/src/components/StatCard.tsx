import React from 'react';

interface StatCardProps {
  title: string;
  subtitle: string;
  value?: string | number;
  trend?: {
    text: string;
    isPositive: boolean;
  };
  icon?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, subtitle, value, trend, icon, children, className = "" }) => {
  return (
    <div className={`glass-panel rounded-3xl p-6 md:p-8 flex flex-col justify-between min-h-[280px] ${className}`}>
      <div className="flex justify-between items-start mb-6">
        <div className="flex flex-col gap-1">
          <h3 className="text-white text-lg font-medium">{title}</h3>
          <p className="text-slate-400 text-sm">{subtitle}</p>
        </div>
        {icon && (
          <div className="p-2 rounded-lg bg-white/5">
            {icon}
          </div>
        )}
      </div>
      
      <div className="flex flex-col gap-6">
        {value && (
          <div className="flex items-end gap-2">
            <span className="text-5xl font-bold text-white tracking-tight">{value}</span>
            {trend && (
              <span className={`mb-2 font-medium text-sm flex items-center ${trend.isPositive ? 'text-green-400' : 'text-red-400'}`}>
                {trend.text}
              </span>
            )}
          </div>
        )}
        {children}
      </div>
    </div>
  );
};

export default StatCard;
