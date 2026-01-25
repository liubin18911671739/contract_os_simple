interface BadgeProps {
  children: React.ReactNode;
  color?: 'red' | 'amber' | 'emerald' | 'blue' | 'gray' | 'purple';
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function Badge({ children, color = 'gray', className = '', size = 'md' }: BadgeProps) {
  const colors = {
    red: 'bg-red-100 text-red-800',
    amber: 'bg-amber-100 text-amber-800',
    emerald: 'bg-emerald-100 text-emerald-800',
    blue: 'bg-blue-100 text-blue-800',
    gray: 'bg-gray-100 text-gray-800',
    purple: 'bg-purple-100 text-purple-800',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-xs',
    lg: 'px-3 py-1 text-sm',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${colors[color]} ${sizes[size]} ${className}`}
    >
      {children}
    </span>
  );
}

export function RiskBadge({ level }: { level: string }) {
  const colorMap: Record<string, 'red' | 'amber' | 'emerald' | 'blue'> = {
    HIGH: 'red',
    MEDIUM: 'amber',
    LOW: 'emerald',
    INFO: 'blue',
  };

  return <Badge color={colorMap[level] || 'gray'}>{level}</Badge>;
}
