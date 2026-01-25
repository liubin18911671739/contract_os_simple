/**
 * Search Results Component
 * Displays KB search results with relevance scores and document info
 */
import { KBSearchResult } from '../../api/kb';
import { Badge } from '../ui/Badge';

interface SearchResultsProps {
  results: KBSearchResult[];
  query: string;
  loading?: boolean;
}

export function SearchResults({ results, query, loading }: SearchResultsProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
        <span className="ml-3 text-gray-600">搜索中...</span>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">未找到相关内容</p>
        <p className="text-sm text-gray-400 mt-2">尝试调整搜索词或选择其他集合</p>
      </div>
    );
  }

  // Function to highlight query terms in text
  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text;

    const terms = query.split(/\s+/).filter(t => t.length > 0);
    if (terms.length === 0) return text;

    const regex = new RegExp(`(${terms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark key={i} className="bg-yellow-200 text-gray-900 px-0.5 rounded">
          {part}
        </mark>
      ) : part
    );
  };

  const getScoreBadge = (score: number) => {
    if (score >= 0.8) return { color: 'emerald', label: '高相关' };
    if (score >= 0.6) return { color: 'blue', label: '相关' };
    if (score >= 0.4) return { color: 'amber', label: '中等' };
    return { color: 'gray', label: '低相关' };
  };

  return (
    <div className="space-y-4">
      <div className="text-sm text-gray-600">
        找到 <span className="font-semibold text-accent">{results.length}</span> 条相关结果
      </div>

      {results.map((result, index) => {
        const scoreConfig = getScoreBadge(result.score);

        return (
          <div
            key={result.chunk_id || index}
            className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between gap-4 mb-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h4 className="font-semibold text-gray-900">{result.doc_title}</h4>
                  <Badge color={scoreConfig.color as any}>{scoreConfig.label}</Badge>
                  {result.collection_id && (
                    <span className="text-xs text-gray-500">
                      相关度: {(result.score * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
                <p className="text-gray-700 text-sm leading-relaxed">
                  {highlightText(result.text, query)}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 mt-3 pt-3 border-t border-gray-100">
              <span className="text-xs text-gray-500">
                版本: {result.doc_version}
              </span>
              {result.doc_id && (
                <button
                  className="text-xs text-accent hover:underline"
                  onClick={() => console.log('View document', result.doc_id)}
                >
                  查看文档
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
