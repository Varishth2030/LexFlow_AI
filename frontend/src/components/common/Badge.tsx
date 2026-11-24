import React from 'react';

type BadgeVariant = 
  | 'default'
  | 'primary'
  | 'success'
  | 'warning'
  | 'danger'
  | 'critical'
  | 'info'
  | 'neutral'
  | 'purple';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  dot?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  className = '',
}) => {
  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5 font-medium',
    md: 'text-xs px-2.5 py-1 font-medium',
  };

  const variantStyles: Record<BadgeVariant, { badge: string; dot: string }> = {
    default: {
      badge: 'bg-slate-100 text-slate-700 border border-slate-200',
      dot: 'bg-slate-500',
    },
    primary: {
      badge: 'bg-blue-50 text-blue-700 border border-blue-200',
      dot: 'bg-blue-500',
    },
    success: {
      badge: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
      dot: 'bg-emerald-500',
    },
    warning: {
      badge: 'bg-amber-50 text-amber-700 border border-amber-200',
      dot: 'bg-amber-500',
    },
    danger: {
      badge: 'bg-rose-50 text-rose-700 border border-rose-200',
      dot: 'bg-rose-500',
    },
    critical: {
      badge: 'bg-red-100 text-red-800 border border-red-300 font-semibold',
      dot: 'bg-red-600',
    },
    info: {
      badge: 'bg-sky-50 text-sky-700 border border-sky-200',
      dot: 'bg-sky-500',
    },
    neutral: {
      badge: 'bg-gray-100 text-gray-600 border border-gray-200',
      dot: 'bg-gray-400',
    },
    purple: {
      badge: 'bg-purple-50 text-purple-700 border border-purple-200',
      dot: 'bg-purple-500',
    },
  };

  const currentVariant = variantStyles[variant] || variantStyles.default;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full ${sizeStyles[size]} ${currentVariant.badge} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${currentVariant.dot}`} />}
      {children}
    </span>
  );
};
