interface BadgeProps {
  children: React.ReactNode;
  color?: 'red' | 'amber' | 'emerald' | 'blue' | 'gray';
}

export function Badge({ children, color = 'gray' }: BadgeProps) {
  const colors = {
    red: 'bg-red-100 text-red-800',
    amber: 'bg-amber-100 text-amber-800',
    emerald: 'bg-emerald-100 text-emerald-800',
    blue: 'bg-blue-100 text-blue-800',
    gray: 'bg-gray-100 text-gray-800',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[color]}`}
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
