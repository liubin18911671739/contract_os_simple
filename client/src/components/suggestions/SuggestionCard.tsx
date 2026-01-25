/**
 * Suggestion Card Component
 * Displays a single suggestion in a card format with action buttons
 */

import { Clock, User, Edit, History, Sparkles } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { Suggestion } from '../../api/suggestions';

interface SuggestionCardProps {
  suggestion: Suggestion;
  onEdit?: (suggestionId: string, currentText: string) => void;
  onViewHistory?: (suggestionId: string) => void;
  compact?: boolean;
  showActions?: boolean;
}

export function SuggestionCard({
  suggestion,
  onEdit,
  onViewHistory,
  compact = false,
  showActions = true,
}: SuggestionCardProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  const getCreatorLabel = (createdBy: string | null) => {
    if (!createdBy) return '系统';
    if (createdBy === 'ai') return 'AI生成';
    if (createdBy === 'ai_fallback') return '备用建议';
    return createdBy;
  };

  return (
    <div className={`bg-purple-50 rounded-lg border border-purple-200 ${
      compact ? 'p-3' : 'p-4'
    }`}>
      {/* Header with type badge and actions */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-lg">💡</span>
          <span className={`font-medium ${
            compact ? 'text-sm' : 'text-sm'
          }`}>
            修改建议
          </span>
          {suggestion.created_by === 'ai' && (
            <Badge color="blue" size="sm">AI生成</Badge>
          )}
          {suggestion.created_by === 'ai_fallback' && (
            <Badge color="amber" size="sm">备用建议</Badge>
          )}
          {suggestion.created_by && suggestion.created_by !== 'ai' && suggestion.created_by !== 'ai_fallback' && (
            <Badge color="emerald" size="sm">人工</Badge>
          )}
        </div>

        {showActions && (
          <div className="flex items-center gap-1 flex-shrink-0">
            {onEdit && (
              <button
                onClick={() => onEdit(suggestion.id, suggestion.suggestion_text)}
                className="p-1.5 text-accent hover:bg-purple-100 rounded transition-colors"
                title="编辑建议"
              >
                <Edit className="w-4 h-4" />
              </button>
            )}
            {onViewHistory && suggestion.revision_count > 0 && (
              <button
                onClick={() => onViewHistory(suggestion.id)}
                className="p-1.5 text-gray-500 hover:bg-purple-100 rounded transition-colors"
                title={`查看历史 (${suggestion.revision_count}个修订)`}
              >
                <History className="w-4 h-4" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Suggestion text */}
      <p className={`text-gray-700 whitespace-pre-wrap ${
        compact ? 'text-xs line-clamp-2' : 'text-sm'
      }`}>
        {suggestion.suggestion_text}
      </p>

      {/* Footer with metadata */}
      {!compact && (
        <div className="flex items-center gap-3 mt-3 pt-2 border-t border-purple-200/50 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <User className="w-3.5 h-3.5" />
            <span>{getCreatorLabel(suggestion.created_by)}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            <span>{formatDate(suggestion.created_at)}</span>
          </div>
          {suggestion.revision_count > 0 && (
            <div className="flex items-center gap-1 text-purple-600">
              <Sparkles className="w-3.5 h-3.5" />
              <span>{suggestion.revision_count}个修订</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * SuggestionList Component
 * Displays multiple suggestion cards
 */

interface SuggestionListProps {
  suggestions: Suggestion[];
  onEdit?: (suggestionId: string, currentText: string) => void;
  onViewHistory?: (suggestionId: string) => void;
  emptyMessage?: string;
  compact?: boolean;
}

export function SuggestionList({
  suggestions,
  onEdit,
  onViewHistory,
  emptyMessage = '暂无修改建议',
  compact = false,
}: SuggestionListProps) {
  if (suggestions.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 text-sm">
        <span className="text-2xl mb-2 block">💡</span>
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${compact ? 'space-y-2' : ''}`}>
      {suggestions.map((suggestion) => (
        <SuggestionCard
          key={suggestion.id}
          suggestion={suggestion}
          onEdit={onEdit}
          onViewHistory={onViewHistory}
          compact={compact}
        />
      ))}
    </div>
  );
}
