interface TimelineProps {
  events: Array<{ ts: string; level: 'info' | 'warning' | 'error'; message: string }>;
}

export function Timeline({ events }: TimelineProps) {
  const levelColors = {
    info: 'border-blue-500 bg-blue-50',
    warning: 'border-amber-500 bg-amber-50',
    error: 'border-red-500 bg-red-50',
  };

  return (
    <div className="space-y-2">
      {events.map((event, index) => (
        <div key={index} className="flex items-start space-x-3">
          <div className={`w-3 h-3 rounded-full border-2 ${levelColors[event.level]} mt-1.5`} />
          <div className="flex-1">
            <div className="text-sm text-gray-900">{event.message}</div>
            <div className="text-xs text-gray-500">{new Date(event.ts).toLocaleString()}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
