/**
 * Log Viewer Component
 * Displays application logs in a dev-friendly format
 */
import { useState, useEffect } from 'react';
import { X, Download, Trash2, Filter, ChevronDown, ChevronUp } from 'lucide-react';
import { logger } from '../utils/logger';

interface LogEntry {
  level: 'debug' | 'info' | 'warn' | 'error';
  timestamp: Date;
  message: string;
  context?: any;
}

export function LogViewer() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState<'all' | 'debug' | 'info' | 'warn' | 'error'>('all');
  const [search, setSearch] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (!isOpen) return;

    // Update logs every second
    const interval = setInterval(() => {
      setLogs(logger.getLogs());
    }, 1000);

    return () => clearInterval(interval);
  }, [isOpen]);

  const filteredLogs = logs.filter(log => {
    if (filter !== 'all' && log.level !== filter) return false;
    if (search && !log.message.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const toggleExpand = (index: number) => {
    setExpanded(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const getLevelColor = (level: string) => {
    const colors = {
      debug: 'text-gray-500',
      info: 'text-blue-500',
      warn: 'text-yellow-500',
      error: 'text-red-500',
    };
    return colors[level as keyof typeof colors] || 'text-gray-500';
  };

  const getLevelBg = (level: string) => {
    const colors = {
      debug: 'bg-gray-100',
      info: 'bg-blue-100',
      warn: 'bg-yellow-100',
      error: 'bg-red-100',
    };
    return colors[level as keyof typeof colors] || 'bg-gray-100';
  };

  if (!isOpen) {
    // Floating toggle button
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 z-50 p-3 bg-blue-500 text-white rounded-full shadow-lg hover:bg-blue-600 transition-colors"
        title="Open Log Viewer"
      >
        <Filter size={20} />
        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
          {logs.length}
        </span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-0 right-0 z-50 w-full max-w-2xl h-96 bg-white border-t shadow-lg flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-100 border-b">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold">Log Viewer</h3>
          <span className="text-sm text-gray-500">({filteredLogs.length} logs)</span>
        </div>
        <div className="flex items-center gap-2">
          {/* Filter buttons */}
          <div className="flex gap-1 mr-2">
            {(['all', 'info', 'warn', 'error'] as const).map(level => (
              <button
                key={level}
                onClick={() => setFilter(level)}
                className={`px-2 py-1 text-xs rounded ${
                  filter === level ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
                }`}
              >
                {level}
              </button>
            ))}
          </div>
          {/* Search */}
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="px-2 py-1 text-sm border rounded"
          />
          {/* Actions */}
          <button
            onClick={() => logger.downloadLogs()}
            className="p-1 hover:bg-gray-200 rounded"
            title="Download logs"
          >
            <Download size={16} />
          </button>
          <button
            onClick={() => {
              logger.clearLogs();
              setLogs([]);
            }}
            className="p-1 hover:bg-gray-200 rounded"
            title="Clear logs"
          >
            <Trash2 size={16} />
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-gray-200 rounded"
            title="Close"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Log entries */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {filteredLogs.length === 0 ? (
          <div className="text-center text-gray-500 py-8">No logs to display</div>
        ) : (
          filteredLogs.map((log, index) => (
            <div
              key={index}
              className={`p-2 rounded ${getLevelBg(log.level)} text-sm`}
            >
              <div
                className="flex items-start gap-2 cursor-pointer"
                onClick={() => toggleExpand(index)}
              >
                <span className="font-mono text-xs text-gray-400">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className={`font-semibold uppercase ${getLevelColor(log.level)}`}>
                  {log.level}
                </span>
                <span className="flex-1">{log.message}</span>
                {log.context && (
                  <span>
                    {expanded.has(index) ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </span>
                )}
              </div>
              {log.context && expanded.has(index) && (
                <div className="mt-2 pl-4 border-l-2 border-gray-300">
                  <pre className="text-xs overflow-auto">
                    {JSON.stringify(log.context, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
