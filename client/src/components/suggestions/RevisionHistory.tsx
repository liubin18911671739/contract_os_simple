/**
 * Revision History Component
 * Displays and manages suggestion revision history
 */

import { useState, useEffect } from 'react';
import { History, Eye, Calendar, ChevronDown, ChevronUp } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { getSuggestionRevisions, SuggestionRevision } from '../../api/suggestions';

interface RevisionHistoryProps {
  suggestionId: string;
  currentText: string;
  isOpen?: boolean;
}

export function RevisionHistory({ suggestionId, currentText, isOpen = false }: RevisionHistoryProps) {
  const [expanded, setExpanded] = useState(isOpen);
  const [revisions, setRevisions] = useState<SuggestionRevision[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (expanded && revisions.length === 0) {
      loadRevisions();
    }
  }, [expanded]);

  const loadRevisions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSuggestionRevisions(suggestionId);
      setRevisions(data);
    } catch (err: any) {
      setError(err.message || '加载修订历史失败');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getCreatorLabel = (createdBy: string | null) => {
    if (!createdBy) return '系统';
    if (createdBy === 'ai') return 'AI生成';
    if (createdBy === 'ai_fallback') return '备用建议';
    return createdBy;
  };

  const getCreatorColor = (createdBy: string | null) => {
    if (!createdBy) return 'gray';
    if (createdBy === 'ai') return 'blue';
    if (createdBy === 'ai_fallback') return 'amber';
    return 'emerald';
  };

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">
            修订历史 ({revisions.length})
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {/* Content */}
      {expanded && (
        <div className="border-t border-gray-200 p-3">
          {loading ? (
            <div className="text-center py-4 text-sm text-gray-500">加载中...</div>
          ) : error ? (
            <div className="text-center py-4 text-sm text-red-500">{error}</div>
          ) : revisions.length === 0 ? (
            <div className="text-center py-4 text-sm text-gray-500">
              暂无修订历史
            </div>
          ) : (
            <div className="space-y-3">
              {/* Current version */}
              <div className="bg-purple-50 rounded-lg border border-purple-200 p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-purple-700">当前版本</span>
                  <Badge color="purple" size="sm">最新</Badge>
                </div>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{currentText}</p>
              </div>

              {/* Past revisions */}
              <div className="space-y-2">
                {revisions
                  .sort((a, b) => b.revision_no - a.revision_no)
                  .map((revision) => (
                    <div
                      key={revision.id}
                      className="bg-white rounded-lg border border-gray-200 p-3"
                    >
                      <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium text-gray-700">
                            修订 #{revision.revision_no}
                          </span>
                          <Badge color={getCreatorColor(revision.created_by)} size="sm">
                            {getCreatorLabel(revision.created_by)}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-gray-500">
                          <Calendar className="w-3 h-3" />
                          <span>{formatDate(revision.created_at)}</span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-2 rounded font-mono text-xs">
                        {revision.suggestion_text}
                      </p>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Compact Revision Badge
 * Shows revision count with hover to see details
 */

interface RevisionBadgeProps {
  count: number;
  onViewDetails?: () => void;
}

export function RevisionBadge({ count, onViewDetails }: RevisionBadgeProps) {
  if (count === 0) {
    return null;
  }

  return (
    <button
      onClick={onViewDetails}
      className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-medium hover:bg-purple-200 transition-colors"
      title="查看修订历史"
    >
      <History className="w-3 h-3" />
      <span>{count}个修订</span>
    </button>
  );
}

/**
 * Revision Timeline Component
 * Visual timeline of suggestion changes
 */

interface RevisionTimelineProps {
  currentText: string;
  revisions: SuggestionRevision[];
}

interface TimelineVersion {
  revision_no: number;
  suggestion_text: string;
  created_at: string;
  created_by: string | null;
  is_current: boolean;
}

export function RevisionTimeline({ currentText, revisions }: RevisionTimelineProps) {
  const allVersions: TimelineVersion[] = [
    {
      revision_no: 0,
      suggestion_text: currentText,
      created_at: new Date().toISOString(),
      created_by: null,
      is_current: true,
    },
    ...revisions.map((r) => ({ ...r, is_current: false })).sort((a, b) => b.revision_no - a.revision_no),
  ];

  return (
    <div className="relative">
      {/* Timeline line */}
      <div className="absolute left-[15px] top-0 bottom-0 w-px bg-gray-200" />

      <div className="space-y-4">
        {allVersions.map((version) => (
          <div key={version.revision_no} className="relative flex items-start gap-4">
            {/* Timeline dot */}
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center z-10 flex-shrink-0 ${
                version.is_current
                  ? 'bg-accent text-white'
                  : 'bg-gray-200 text-gray-600'
              }`}
            >
              {version.is_current ? (
                <Eye className="w-4 h-4" />
              ) : (
                <span className="text-xs font-medium">{version.revision_no}</span>
              )}
            </div>

            {/* Content */}
            <div className="flex-1 bg-white rounded-lg border border-gray-200 p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  {version.is_current ? '当前版本' : `修订 #${version.revision_no}`}
                </span>
                {!version.is_current && version.created_at && (
                  <span className="text-xs text-gray-500">
                    {new Date(version.created_at).toLocaleString('zh-CN')}
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-700 whitespace-pre-wrap font-mono bg-gray-50 p-2 rounded">
                {version.suggestion_text}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
