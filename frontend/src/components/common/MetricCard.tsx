import React from 'react';
import { Card } from './Card';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
  iconBg?: string;
  subtitle?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  changeType = 'neutral',
  icon,
  iconBg = 'bg-brand-50 text-brand-600',
  subtitle,
}) => {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{title}</p>
          <h4 className="text-2xl font-bold text-slate-900 mt-1.5">{value}</h4>
        </div>
        <div className={`p-2.5 rounded-xl ${iconBg} shrink-0`}>
          {icon}
        </div>
      </div>

      {(change || subtitle) && (
        <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
          {change && (
            <div className="flex items-center gap-1 font-medium">
              {changeType === 'positive' && (
                <span className="text-emerald-600 flex items-center">
                  <ArrowUpRight className="w-3.5 h-3.5" /> {change}
                </span>
              )}
              {changeType === 'negative' && (
                <span className="text-rose-600 flex items-center">
                  <ArrowDownRight className="w-3.5 h-3.5" /> {change}
                </span>
              )}
              {changeType === 'neutral' && <span className="text-slate-500">{change}</span>}
              <span className="text-slate-400 font-normal">vs last month</span>
            </div>
          )}
          {subtitle && <span className="text-slate-400">{subtitle}</span>}
        </div>
      )}
    </Card>
  );
};
