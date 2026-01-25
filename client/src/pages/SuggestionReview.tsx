/**
 * Suggestion Review Page
 * Dedicated page for reviewing and editing all suggestions for a task
 */

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Filter,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle,
  Clock,
} from 'lucide-react';
import { getTask, getTaskClauses } from '../api/tasks';
import { getEvidenceChain, adjustRiskLevel, EvidenceChain as EvidenceChainType, type RiskAdjustment } from '../api/suggestions';
import { Button } from '../components/ui/Button';
import { RiskBadge, Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { Modal } from '../components/ui/Modal';
import { EvidenceChain } from '../components/suggestions/EvidenceChain';

interface ClauseWithRisk {
  id: string;
  clause_id: string;
  title: string;
  text?: string;
  summary?: string;
  risk_id?: string;
  risk_level?: string;
  risk_type?: string;
  status?: string;
  confidence?: number;
}

interface ReviewItem extends ClauseWithRisk {
  evidenceChain?: EvidenceChainType;
  suggestions?: any[];
  isLoading?: boolean;
}

export default function SuggestionReview() {
  const { taskId } = useParams<{ taskId: string }>();

  const [task, setTask] = useState<any>(null);
  const [clauses, setClauses] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [riskLevelFilter, setRiskLevelFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [reviewedFilter, setReviewedFilter] = useState<string>('');

  // Evidence chain modal
  const [selectedRisk, setSelectedRisk] = useState<{
    clauseId: string;
    clauseTitle: string;
    riskId: string;
  } | null>(null);
  const [evidenceChain, setEvidenceChain] = useState<EvidenceChainType | null>(null);
  const [loadingEvidenceChain, setLoadingEvidenceChain] = useState(false);

  // Inline expansion
  const [expandedClauses, setExpandedClauses] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!taskId) return;
    load();
  }, [taskId]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [taskData, clausesData] = await Promise.all([
        getTask(taskId!),
        getTaskClauses(taskId!),
      ]);

      setTask(taskData);

      // Transform clauses into review items
      const reviewItems: ReviewItem[] = (clausesData as any[])
        .filter((c) => c.risk_id) // Only include clauses with risks
        .map((c) => ({
          ...c,
          isLoading: false,
        }));

      setClauses(reviewItems);
    } catch (err: any) {
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }

  // Toggle clause expansion
  const toggleExpansion = async (clauseId: string, riskId: string) => {
    const newExpanded = new Set(expandedClauses);
    const isExpanding = !newExpanded.has(clauseId);

    if (isExpanding) {
      newExpanded.add(clauseId);

      // Load evidence chain if not already loaded
      const itemIndex = clauses.findIndex((c) => c.id === clauseId);
      if (itemIndex >= 0 && !clauses[itemIndex].evidenceChain) {
        setClauses((prev) =>
          prev.map((c, i) =>
            i === itemIndex ? { ...c, isLoading: true } : c
          )
        );

        try {
          const chain = await getEvidenceChain(riskId);
          setClauses((prev) =>
            prev.map((c, i) =>
              i === itemIndex
                ? { ...c, evidenceChain: chain, suggestions: chain.suggestions, isLoading: false }
                : c
            )
          );
        } catch (err) {
          console.error('Failed to load evidence chain:', err);
          setClauses((prev) =>
            prev.map((c, i) =>
              i === itemIndex ? { ...c, isLoading: false } : c
            )
          );
        }
      }
    } else {
      newExpanded.delete(clauseId);
    }

    setExpandedClauses(newExpanded);
  };

  // Open modal for detailed review
  const openEvidenceModal = async (clauseId: string, clauseTitle: string, riskId: string) => {
    setSelectedRisk({ clauseId, clauseTitle, riskId });
    setEvidenceChain(null);
    setLoadingEvidenceChain(true);

    try {
      const chain = await getEvidenceChain(riskId);
      setEvidenceChain(chain);
    } catch (err) {
      console.error('Failed to load evidence chain:', err);
    } finally {
      setLoadingEvidenceChain(false);
    }
  };

  // Handle risk level adjustment
  const handleAdjustRiskLevel = async (riskId: string, newLevel: string, reason?: string) => {
    try {
      const adjustment: RiskAdjustment = {
        risk_level: newLevel,
        reason,
      };
      await adjustRiskLevel(riskId, adjustment);

      // Refresh the data
      if (selectedRisk && selectedRisk.riskId === riskId) {
        const chain = await getEvidenceChain(riskId);
        setEvidenceChain(chain);
      }

      // Update clauses list
      setClauses((prev) =>
        prev.map((c) =>
          c.risk_id === riskId ? { ...c, risk_level: newLevel } : c
        )
      );
    } catch (err) {
      console.error('Failed to adjust risk level:', err);
    }
  };

  // Handle suggestion edit
  const handleEditSuggestion = async (_suggestionId: string, _newText: string) => {
    // Close modal and reload
    setSelectedRisk(null);
    // Reload expanded items
    for (const clauseId of expandedClauses) {
      const item = clauses.find((c) => c.id === clauseId);
      if (item?.risk_id) {
        try {
          const chain = await getEvidenceChain(item.risk_id);
          setClauses((prev) =>
            prev.map((c) =>
              c.id === clauseId
                ? { ...c, evidenceChain: chain, suggestions: chain.suggestions }
                : c
            )
          );
        } catch (err) {
          console.error('Failed to reload:', err);
        }
      }
    }
  };

  // Filter clauses
  const filteredClauses = clauses.filter((c) => {
    if (riskLevelFilter && c.risk_level !== riskLevelFilter) return false;
    if (statusFilter && c.status !== statusFilter) return false;
    if (reviewedFilter === 'reviewed' && c.status !== 'CONFIRMED') return false;
    if (reviewedFilter === 'unreviewed' && c.status === 'CONFIRMED') return false;
    return true;
  });

  // Stats
  const stats = {
    total: clauses.length,
    high: clauses.filter((c) => c.risk_level === 'HIGH').length,
    medium: clauses.filter((c) => c.risk_level === 'MEDIUM').length,
    low: clauses.filter((c) => c.risk_level === 'LOW').length,
    confirmed: clauses.filter((c) => c.status === 'CONFIRMED').length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (error) {
    return <Alert type="error">{error}</Alert>;
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link to={`/results/${taskId}`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-1" />
              返回结果
            </Button>
          </Link>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">建议审核</h2>
            {task && (
              <p className="text-sm text-gray-500">任务: {task.contract_version_id?.slice(0, 8)}</p>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">总风险</div>
          <div className="text-xl font-bold text-gray-900">{stats.total}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">高风险</div>
          <div className="text-xl font-bold text-red-600">{stats.high}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">中风险</div>
          <div className="text-xl font-bold text-amber-600">{stats.medium}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">低风险</div>
          <div className="text-xl font-bold text-emerald-600">{stats.low}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-500">已确认</div>
          <div className="text-xl font-bold text-blue-600">{stats.confirmed}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">筛选:</span>
          </div>
          <select
            value={riskLevelFilter}
            onChange={(e) => setRiskLevelFilter(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
          >
            <option value="">所有风险等级</option>
            <option value="HIGH">高风险</option>
            <option value="MEDIUM">中风险</option>
            <option value="LOW">低风险</option>
            <option value="INFO">信息</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
          >
            <option value="">所有状态</option>
            <option value="CONFIRMED">已确认</option>
            <option value="PENDING">待审核</option>
            <option value="DISMISSED">已忽略</option>
          </select>
          <select
            value={reviewedFilter}
            onChange={(e) => setReviewedFilter(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
          >
            <option value="">全部</option>
            <option value="unreviewed">未审核</option>
            <option value="reviewed">已审核</option>
          </select>
          <div className="ml-auto text-sm text-gray-500">
            显示 {filteredClauses.length} / {clauses.length} 条
          </div>
        </div>
      </div>

      {/* Review List */}
      <div className="space-y-4">
        {filteredClauses.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
            <AlertCircle className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p>没有找到符合条件的风险</p>
          </div>
        ) : (
          filteredClauses.map((item) => {
            const isExpanded = expandedClauses.has(item.id);

            return (
              <div key={item.id} className="bg-white rounded-lg shadow border border-gray-200">
                {/* Summary bar */}
                <div className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1">
                    {/* Expand button */}
                    <button
                      onClick={() => toggleExpansion(item.id, item.risk_id!)}
                      className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5" />
                      ) : (
                        <ChevronDown className="w-5 h-5" />
                      )}
                    </button>

                    {/* Status indicator */}
                    <div>
                      {item.status === 'CONFIRMED' ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : item.status === 'DISMISSED' ? (
                        <AlertCircle className="w-5 h-5 text-gray-400" />
                      ) : (
                        <Clock className="w-5 h-5 text-amber-500" />
                      )}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-gray-900">
                          {item.title || 'Unnamed Clause'}
                        </span>
                        {item.risk_level && <RiskBadge level={item.risk_level} />}
                        {item.risk_type && (
                          <Badge color="blue" size="sm">{item.risk_type}</Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 truncate">{item.summary}</p>
                    </div>

                    {/* Confidence */}
                    {item.confidence !== undefined && (
                      <div className="text-sm text-gray-500">
                        置信度: {(item.confidence * 100).toFixed(0)}%
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 ml-4">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => openEvidenceModal(item.id, item.title || 'Unnamed Clause', item.risk_id!)}
                    >
                      详细审查
                    </Button>
                    <Link to={`/review/${taskId}`}>
                      <Button size="sm" variant="ghost">
                        处理
                      </Button>
                    </Link>
                  </div>
                </div>

                {/* Expanded content */}
                {isExpanded && (
                  <div className="border-t border-gray-200 p-4 bg-gray-50">
                    {item.isLoading ? (
                      <div className="text-center py-8 text-gray-500">加载中...</div>
                    ) : item.evidenceChain ? (
                      <EvidenceChain
                        evidenceChain={item.evidenceChain}
                        onEditSuggestion={handleEditSuggestion}
                        onAdjustRiskLevel={handleAdjustRiskLevel}
                      />
                    ) : (
                      <div className="text-center py-8 text-gray-500">无法加载证据链</div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Evidence Chain Modal */}
      {selectedRisk && (
        <Modal
          isOpen={!!selectedRisk}
          onClose={() => setSelectedRisk(null)}
          title={`详细审查: ${selectedRisk.clauseTitle}`}
          size="xl"
        >
          <div className="max-h-[70vh] overflow-y-auto">
            {loadingEvidenceChain ? (
              <div className="text-center py-8 text-gray-500">加载中...</div>
            ) : evidenceChain ? (
              <EvidenceChain
                evidenceChain={evidenceChain}
                onEditSuggestion={handleEditSuggestion}
                onAdjustRiskLevel={handleAdjustRiskLevel}
              />
            ) : (
              <div className="text-center py-8 text-gray-500">无法加载证据链</div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
