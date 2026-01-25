/**
 * Evidence Chain Component
 * Displays the complete evidence chain for a risk with timeline visualization
 */

import { useState } from 'react';
import { ChevronDown, ChevronRight, File, Scale, BookOpen, AlertCircle, Check } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { EvidenceChain as EvidenceChainType, Suggestion } from '../../api/suggestions';
import { RiskLevelAdjuster } from './RiskLevelAdjuster';
import { SuggestionEditor, SuggestionDiffViewer } from './SuggestionEditor';

interface EvidenceChainProps {
  evidenceChain: EvidenceChainType;
  onEditSuggestion?: (suggestionId: string, currentText: string) => void;
  onAdjustRiskLevel?: (riskId: string, newLevel: string, reason?: string) => void;
}

interface TimelineItemProps {
  type: 'risk' | 'clause' | 'rule' | 'citation' | 'evidence' | 'suggestion';
  title: string;
  children: React.ReactNode;
  badge?: React.ReactNode;
  expandable?: boolean;
  defaultExpanded?: boolean;
}

function TimelineItem({ type, title, children, badge, expandable = false, defaultExpanded = false }: TimelineItemProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const typeColors = {
    risk: 'bg-red-100 text-red-700 border-red-200',
    clause: 'bg-gray-100 text-gray-700 border-gray-200',
    rule: 'bg-amber-100 text-amber-700 border-amber-200',
    citation: 'bg-blue-100 text-blue-700 border-blue-200',
    evidence: 'bg-green-100 text-green-700 border-green-200',
    suggestion: 'bg-purple-100 text-purple-700 border-purple-200',
  };

  const typeIcons = {
    risk: AlertCircle,
    clause: File,
    rule: Scale,
    citation: BookOpen,
    evidence: Check,
    suggestion: "💡",
  };

  const Icon = typeIcons[type];

  return (
    <div className={`ml-6 relative ${typeColors[type]} rounded-lg border`}>
      {expandable ? (
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center gap-2 px-3 py-2 hover:bg-black/5 transition-colors"
        >
          <Icon className="w-4 h-4" />
          <span className="font-medium text-sm">{title}</span>
          {badge}
          {expanded ? (
            <ChevronDown className="w-4 h-4 ml-auto" />
          ) : (
            <ChevronRight className="w-4 h-4 ml-auto" />
          )}
        </button>
      ) : (
        <div className="flex items-center gap-2 px-3 py-2">
          <Icon className="w-4 h-4" />
          <span className="font-medium text-sm">{title}</span>
          {badge}
        </div>
      )}
      {expandable && expanded && (
        <div className="px-3 pb-3 text-sm">{children}</div>
      )}
    </div>
  );
}

interface SuggestionItemProps {
  suggestion: Suggestion;
  onViewHistory?: (suggestionId: string) => void;
  onEdit?: (suggestionId: string, currentText: string) => void;
}

function SuggestionItem({ suggestion, onViewHistory, onEdit }: SuggestionItemProps) {
  return (
    <div className="ml-6 bg-purple-50 rounded-lg border border-purple-200 p-4">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">💡</span>
          <span className="font-medium text-sm">修改建议</span>
          {suggestion.created_by === 'ai' && (
            <Badge color="blue">AI生成</Badge>
          )}
          {suggestion.created_by === 'ai_fallback' && (
            <Badge color="amber">备用建议</Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {onEdit && (
            <button
              onClick={() => onEdit(suggestion.id, suggestion.suggestion_text)}
              className="text-xs text-accent hover:underline"
            >
              编辑
            </button>
          )}
          {onViewHistory && (
            <button
              onClick={() => onViewHistory(suggestion.id)}
              className="text-xs text-gray-500 hover:underline"
            >
              历史({suggestion.revision_count})
            </button>
          )}
        </div>
      </div>
      <p className="text-sm text-gray-700 whitespace-pre-wrap">{suggestion.suggestion_text}</p>
    </div>
  );
}

export function EvidenceChain({
  evidenceChain,
  onEditSuggestion,
  onAdjustRiskLevel,
}: EvidenceChainProps) {
  const [editingSuggestion, setEditingSuggestion] = useState<{
    id: string;
    text: string;
  } | null>(null);
  const [showHistoryFor, setShowHistoryFor] = useState<string | null>(null);

  // Get color for risk level
  const getRiskColor = (level: string): 'red' | 'amber' | 'emerald' | 'blue' | 'gray' => {
    const colors: Record<string, 'red' | 'amber' | 'emerald' | 'blue' | 'gray'> = {
      HIGH: 'red',
      MEDIUM: 'amber',
      LOW: 'emerald',
      INFO: 'blue',
    };
    return colors[level] || 'gray';
  };

  // Handle suggestion edit
  const handleEditClick = (suggestionId: string, currentText: string) => {
    setEditingSuggestion({ id: suggestionId, text: currentText });
  };

  const handleSaveEdit = async (suggestionId: string, newText: string) => {
    // API call will be handled by SuggestionEditor component
    if (onEditSuggestion) {
      await onEditSuggestion(suggestionId, newText);
    }
    setEditingSuggestion(null);
  };

  const handleCancelEdit = () => {
    setEditingSuggestion(null);
  };

  // Handle view history - open the diff viewer
  const handleViewHistory = (suggestionId: string) => {
    setShowHistoryFor(suggestionId);
  };

  // Handle risk level adjustment
  const handleAdjustLevel = async (newLevel: string) => {
    if (onAdjustRiskLevel && evidenceChain.risk_id) {
      await onAdjustRiskLevel(evidenceChain.risk_id, newLevel);
    }
  };

  const hasAdjustment = evidenceChain.original_risk_level &&
    evidenceChain.original_risk_level !== evidenceChain.risk_level;

  return (
    <>
    <div className="space-y-4">
      {/* Risk Summary */}
      <TimelineItem
        type="risk"
        title="风险识别"
        badge={
          <Badge color={getRiskColor(evidenceChain.risk_level)}>
            {evidenceChain.risk_level}
          </Badge>
        }
        expandable
        defaultExpanded
      >
        <div className="space-y-2">
          <p className="text-gray-700">{evidenceChain.risk_summary}</p>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>类型: {evidenceChain.risk_type}</span>
            <span>置信度: {(evidenceChain.confidence * 100).toFixed(0)}%</span>
            <span>状态: {evidenceChain.status}</span>
          </div>
          {/* Risk Level Adjuster */}
          {onAdjustRiskLevel && evidenceChain.risk_id && (
            <div className="mt-2 pt-2 border-t border-black/10">
              <RiskLevelAdjuster
                riskId={evidenceChain.risk_id}
                currentLevel={evidenceChain.risk_level as 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'}
                originalLevel={evidenceChain.original_risk_level as ('HIGH' | 'MEDIUM' | 'LOW' | 'INFO') | undefined}
                onAdjusted={handleAdjustLevel}
              />
            </div>
          )}
        </div>
      </TimelineItem>

      {/* Clause */}
      {evidenceChain.clause && (
        <TimelineItem type="clause" title="合同条款" expandable>
          <div className="space-y-2">
            {evidenceChain.clause.title && (
              <div className="font-medium text-gray-900">{evidenceChain.clause.title}</div>
            )}
            <div className="bg-gray-50 p-3 rounded text-sm text-gray-700 whitespace-pre-wrap font-mono">
              {evidenceChain.clause.text}
            </div>
            {evidenceChain.clause.page_ref && (
              <div className="text-xs text-gray-500">引用: {evidenceChain.clause.page_ref}</div>
            )}
          </div>
        </TimelineItem>
      )}

      {/* Rule Hits */}
      {evidenceChain.rule_hits.length > 0 && (
        <TimelineItem
          type="rule"
          title={`规则匹配 (${evidenceChain.rule_hits.length}条)`}
          expandable
        >
          <div className="space-y-2">
            {evidenceChain.rule_hits.map((hit) => (
              <div key={hit.id} className="bg-white p-2 rounded border">
                <div className="font-medium text-xs text-gray-900 mb-1">
                  {hit.rule_name}
                </div>
                <div className="text-xs text-gray-600 font-mono">
                  匹配: "{hit.matched_text}"
                </div>
              </div>
            ))}
          </div>
        </TimelineItem>
      )}

      {/* KB Citations */}
      {evidenceChain.kb_citations.length > 0 && (
        <TimelineItem
          type="citation"
          title={`知识库引用 (${evidenceChain.kb_citations.length}条)`}
          expandable
        >
          <div className="space-y-3">
            {evidenceChain.kb_citations.map((citation) => (
              <div
                key={citation.id}
                className="bg-white p-3 rounded border border-gray-200"
              >
                {citation.document && (
                  <div className="flex items-center gap-2 mb-2">
                    <File className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-medium text-gray-900">
                      {citation.document.title}
                    </span>
                    <Badge color="blue">{citation.document.doc_type}</Badge>
                  </div>
                )}
                <div className="text-sm text-gray-700 mb-2">
                  "{citation.quote_text}"
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span>相似度: {(citation.score * 100).toFixed(0)}%</span>
                  {citation.doc_version && <span>版本: v{citation.doc_version}</span>}
                </div>
              </div>
            ))}
          </div>
        </TimelineItem>
      )}

      {/* Evidences */}
      {evidenceChain.evidences.length > 0 && (
        <TimelineItem
          type="evidence"
          title={`证据 (${evidenceChain.evidences.length}条)`}
          expandable
        >
          <div className="space-y-2">
            {evidenceChain.evidences.map((ev) => (
              <div key={ev.id} className="bg-white p-2 rounded border">
                <div className="text-xs font-medium text-gray-500 mb-1">
                  来源: {ev.source_type}
                </div>
                <div className="text-sm text-gray-700 font-mono">
                  "{ev.quote_text.slice(0, 200)}..."
                </div>
              </div>
            ))}
          </div>
        </TimelineItem>
      )}

      {/* Suggestions */}
      {evidenceChain.suggestions.length > 0 && (
        <TimelineItem
          type="suggestion"
          title={`修改建议 (${evidenceChain.suggestions.length}条)`}
        >
          <div className="space-y-3">
            {evidenceChain.suggestions.map((suggestion) => (
              <SuggestionItem
                key={suggestion.id}
                suggestion={suggestion}
                onEdit={handleEditClick}
                onViewHistory={handleViewHistory}
              />
            ))}
          </div>
        </TimelineItem>
      )}

      {/* Adjustment Info */}
      {hasAdjustment && (
        <div className="ml-6 text-xs text-gray-500 bg-gray-50 px-3 py-2 rounded">
          {evidenceChain.adjusted_by && (
            <span>调整人: {evidenceChain.adjusted_by} • </span>
          )}
          {evidenceChain.adjusted_at && (
            <span>调整时间: {new Date(evidenceChain.adjusted_at).toLocaleString('zh-CN')}</span>
          )}
          {evidenceChain.adjustment_reason && (
            <span>原因: {evidenceChain.adjustment_reason}</span>
          )}
        </div>
      )}
    </div>

    {/* Suggestion Editor Modal */}
    {editingSuggestion && (
      <SuggestionEditor
        isOpen={!!editingSuggestion}
        onClose={handleCancelEdit}
        onSave={handleSaveEdit}
        suggestionId={editingSuggestion.id}
        initialText={editingSuggestion.text}
        riskSummary={evidenceChain.risk_summary}
        clauseText={evidenceChain.clause?.text}
      />
    )}

    {/* Revision History Modal */}
    {showHistoryFor && (
      <SuggestionDiffViewer
        isOpen={!!showHistoryFor}
        onClose={() => setShowHistoryFor(null)}
        currentText={evidenceChain.suggestions.find(s => s.id === showHistoryFor)?.suggestion_text || ''}
        revisions={[]}
      />
    )}
    </>
  );
}
