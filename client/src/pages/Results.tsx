import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import React from 'react';
import { Trash2, ChevronDown, ChevronUp, Lightbulb } from 'lucide-react';
import {
  getTask,
  getTaskSummary,
  getTaskClauses,
  generateReport,
  getReportDownloadUrl,
  deleteTask,
} from '../api/tasks';
import { getEvidenceChain, getSuggestions, EvidenceChain as EvidenceChainType } from '../api/suggestions';
import { Button } from '../components/ui/Button';
import { RiskBadge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { Modal } from '../components/ui/Modal';
import { EvidenceChain } from '../components/suggestions/EvidenceChain';
import { SuggestionCard } from '../components/suggestions/SuggestionCard';
import {
  Table,
  TableHead,
  TableHeader,
  TableBody,
  TableRow,
  TableCell,
} from '../components/ui/Table';

export default function Results() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [task, setTask] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [clauses, setClauses] = useState<any[]>([]);
  const [filter, setFilter] = useState<string>('');
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportMessage, setReportMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Suggestion and evidence chain state
  const [expandedClauses, setExpandedClauses] = useState<Set<string>>(new Set());
  const [clauseSuggestions, setClauseSuggestions] = useState<Map<string, any[]>>(new Map());
  const [loadingSuggestions, setLoadingSuggestions] = useState<Set<string>>(new Set());

  // Evidence chain modal state
  const [evidenceChainModal, setEvidenceChainModal] = useState<{
    riskId: string;
    clauseTitle: string;
  } | null>(null);
  const [evidenceChain, setEvidenceChain] = useState<EvidenceChainType | null>(null);
  const [loadingEvidenceChain, setLoadingEvidenceChain] = useState(false);

  useEffect(() => {
    if (!taskId) return;
    load();
  }, [taskId, filter]);

  async function load() {
    try {
      const [taskData, summaryData, clausesData] = await Promise.all([
        getTask(taskId!),
        getTaskSummary(taskId!),
        getTaskClauses(taskId!, { risk_level: filter || undefined }),
      ]);
      setTask(taskData);
      setSummary(summaryData);
      setClauses(clausesData as any[]);
    } catch (error) {
      console.error('Failed to load results:', error);
    }
  }

  async function handleDeleteTask() {
    if (!confirm('确定要删除此任务及其所有相关数据吗？此操作不可恢复。')) return;

    setDeleteLoading(true);
    try {
      await deleteTask(taskId!);
      navigate('/');
    } catch (error: any) {
      setReportMessage({
        type: 'error',
        text: `删除任务失败: ${error.message || '未知错误'}`,
      });
    } finally {
      setDeleteLoading(false);
    }
  }

  // Toggle clause expansion to show suggestions
  const toggleClauseExpansion = async (clauseId: string, riskId: string | null) => {
    const newExpanded = new Set(expandedClauses);
    const isExpanding = !newExpanded.has(clauseId);

    if (isExpanding) {
      newExpanded.add(clauseId);
      // Load suggestions for this clause's risk
      if (riskId && !clauseSuggestions.has(clauseId)) {
        setLoadingSuggestions((prev) => new Set(prev).add(clauseId));
        try {
          const suggestions = await getSuggestions(riskId);
          setClauseSuggestions((prev) => new Map(prev).set(clauseId, suggestions));
        } catch (error) {
          console.error('Failed to load suggestions:', error);
        } finally {
          setLoadingSuggestions((prev) => {
            const next = new Set(prev);
            next.delete(clauseId);
            return next;
          });
        }
      }
    } else {
      newExpanded.delete(clauseId);
    }
    setExpandedClauses(newExpanded);
  };

  // View evidence chain for a risk
  const viewEvidenceChain = async (riskId: string, clauseTitle: string) => {
    setEvidenceChainModal({ riskId, clauseTitle });
    setEvidenceChain(null);
    setLoadingEvidenceChain(true);
    try {
      const chain = await getEvidenceChain(riskId);
      setEvidenceChain(chain);
    } catch (error) {
      console.error('Failed to load evidence chain:', error);
      setReportMessage({
        type: 'error',
        text: '加载证据链失败',
      });
      setEvidenceChainModal(null);
    } finally {
      setLoadingEvidenceChain(false);
    }
  };

  // Handle editing a suggestion (delegate to parent component)
  const handleEditSuggestion = async (_suggestionId: string, _newText: string) => {
    // This will be handled by the EvidenceChain component's internal logic
    // For now, just close the modal and reload
    setEvidenceChainModal(null);
    // Reload suggestions for expanded clauses
    for (const [clauseId, riskId] of clauses.map((c) => [c.id, c.risk_id])) {
      if (expandedClauses.has(clauseId) && riskId) {
        setLoadingSuggestions((prev) => new Set(prev).add(clauseId));
        try {
          const suggestions = await getSuggestions(riskId);
          setClauseSuggestions((prev) => new Map(prev).set(clauseId, suggestions));
        } catch (error) {
          console.error('Failed to reload suggestions:', error);
        } finally {
          setLoadingSuggestions((prev) => {
            const next = new Set(prev);
            next.delete(clauseId);
            return next;
          });
        }
      }
    }
  };

  // Handle adjusting risk level
  const handleAdjustRiskLevel = async (riskId: string, newLevel: string, reason?: string) => {
    // This will be handled by the EvidenceChain component
    // After adjustment, reload the evidence chain
    if (evidenceChainModal) {
      setLoadingEvidenceChain(true);
      try {
        const chain = await getEvidenceChain(riskId);
        setEvidenceChain(chain);
        // Update summary to reflect changes
        load();
      } catch (error) {
        console.error('Failed to reload evidence chain:', error);
      } finally {
        setLoadingEvidenceChain(false);
      }
    }
  };

  async function handleGenerateReport(format: 'html' | 'json') {
    setGeneratingReport(true);
    setReportMessage(null);

    try {
      const result: any = await generateReport(taskId!, format);

      // Show success message with download option
      setReportMessage({
        type: 'success',
        text: `Report generated successfully! Report ID: ${result.reportId}`,
      });

      // Auto-open download link after short delay
      setTimeout(async () => {
        const downloadUrl = await getReportDownloadUrl(result.reportId);
        window.open(downloadUrl, '_blank');
      }, 1000);
    } catch (error: any) {
      setReportMessage({
        type: 'error',
        text: `Failed to generate report: ${error.message || 'Unknown error'}`,
      });
    } finally {
      setGeneratingReport(false);
    }
  }

  if (!task || !summary) {
    return <div className="text-center py-12">Loading...</div>;
  }

  const isTaskComplete = task.status === 'DONE';

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Analysis Results</h2>
        <div className="flex gap-2">
          {isTaskComplete && (
            <>
              <Button
                variant="secondary"
                onClick={() => handleGenerateReport('html')}
                disabled={generatingReport}
              >
                {generatingReport ? 'Generating...' : '📄 HTML Report'}
              </Button>
              <Button onClick={() => handleGenerateReport('json')} disabled={generatingReport}>
                {generatingReport ? 'Generating...' : '📊 JSON Report'}
              </Button>
            </>
          )}
          <Button
            variant="ghost"
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
            onClick={handleDeleteTask}
            disabled={deleteLoading}
            title="删除任务"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
          <Button variant="ghost" onClick={() => navigate('/')}>
            Back to Dashboard
          </Button>
        </div>
      </div>

      {reportMessage && <Alert type={reportMessage.type}>{reportMessage.text}</Alert>}

      {!isTaskComplete && (
        <Alert type="info">
          Task is still in progress. Reports can be generated once analysis is complete. Current
          status: <strong>{task.status}</strong> ({task.progress}%)
        </Alert>
      )}

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500">High Risks</div>
          <div className="text-2xl font-bold text-red-600">{summary.high_risks || 0}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500">Medium Risks</div>
          <div className="text-2xl font-bold text-amber-600">{summary.medium_risks || 0}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500">Low Risks</div>
          <div className="text-2xl font-bold text-emerald-600">{summary.low_risks || 0}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500">Clauses</div>
          <div className="text-2xl font-bold text-gray-900">{summary.clause_count || 0}</div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">Risks by Clause</h3>
            <div className="flex items-center gap-3">
              <Link to={`/suggestion-review/${taskId}`}>
                <Button size="sm" variant="accent">
                  建议审核
                </Button>
              </Link>
              <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">All Levels</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
              <option value="INFO">Info</option>
            </select>
            </div>
          </div>
        </div>

        <Table>
          <TableHead>
            <TableHeader>Clause</TableHeader>
            <TableHeader>Summary</TableHeader>
            <TableHeader>Risk Level</TableHeader>
            <TableHeader>Status</TableHeader>
            <TableHeader>Actions</TableHeader>
          </TableHead>
          <TableBody>
            {clauses.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-gray-500">
                  No risks found
                </TableCell>
              </TableRow>
            ) : (
              clauses.map((clause: any) => {
                const isExpanded = expandedClauses.has(clause.id);
                const suggestions = clauseSuggestions.get(clause.id) || [];
                const isLoadingSuggestions = loadingSuggestions.has(clause.id);

                return (
                  <React.Fragment key={clause.id}>
                    {/* Main row */}
                    <TableRow>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {clause.risk_id && (
                            <button
                              onClick={() => toggleClauseExpansion(clause.id, clause.risk_id)}
                              className="text-gray-400 hover:text-gray-600 transition-colors"
                            >
                              {isExpanded ? (
                                <ChevronUp className="w-4 h-4" />
                              ) : (
                                <ChevronDown className="w-4 h-4" />
                              )}
                            </button>
                          )}
                          <div>
                            <div className="font-medium">{clause.title || 'Unnamed Clause'}</div>
                            <div className="text-xs text-gray-500">{clause.clause_id}</div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="max-w-md truncate">{clause.summary || 'No risk detected'}</div>
                      </TableCell>
                      <TableCell>
                        {clause.risk_level ? <RiskBadge level={clause.risk_level} /> : '-'}
                      </TableCell>
                      <TableCell>
                        <span
                          className={`text-xs px-2 py-1 rounded-full ${
                            clause.status === 'CONFIRMED'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {clause.status || 'PENDING'}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {clause.risk_id && (
                            <>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => viewEvidenceChain(clause.risk_id, clause.title || 'Unnamed Clause')}
                              >
                                证据链
                              </Button>
                              <Link to={`/review/${taskId}`}>
                                <Button size="sm" variant="ghost">
                                  Review
                                </Button>
                              </Link>
                            </>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>

                    {/* Expanded row with suggestions */}
                    {isExpanded && clause.risk_id && (
                      <TableRow>
                        <TableCell colSpan={5} className="bg-gray-50">
                          <div className="py-3 px-4">
                            <div className="flex items-center gap-2 mb-3">
                              <Lightbulb className="w-4 h-4 text-purple-600" />
                              <span className="text-sm font-medium text-gray-700">修改建议</span>
                              <span className="text-xs text-gray-500">({suggestions.length}条)</span>
                            </div>
                            {isLoadingSuggestions ? (
                              <div className="text-sm text-gray-500">加载中...</div>
                            ) : suggestions.length > 0 ? (
                              <div className="grid grid-cols-1 gap-3">
                                {suggestions.map((suggestion: any) => (
                                  <SuggestionCard
                                    key={suggestion.id}
                                    suggestion={suggestion}
                                    compact
                                    showActions={false}
                                  />
                                ))}
                                <Button
                                  size="sm"
                                  variant="secondary"
                                  onClick={() => viewEvidenceChain(clause.risk_id, clause.title || 'Unnamed Clause')}
                                  className="w-full"
                                >
                                  查看完整证据链和编辑建议
                                </Button>
                              </div>
                            ) : (
                              <div className="text-sm text-gray-500">暂无修改建议</div>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </TableBody>
        </Table>

        {/* Evidence Chain Modal */}
        {evidenceChainModal && (
          <Modal
            isOpen={!!evidenceChainModal}
            onClose={() => setEvidenceChainModal(null)}
            title={`证据链: ${evidenceChainModal.clauseTitle}`}
            size="xl"
          >
            <div className="max-h-[70vh] overflow-y-auto">
              {loadingEvidenceChain ? (
                <div className="text-center py-8 text-gray-500">加载证据链中...</div>
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

      {isTaskComplete && (
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-medium text-blue-900 mb-2">📥 Reports</h3>
          <p className="text-sm text-blue-800 mb-3">
            Generate downloadable reports in HTML or JSON format. HTML reports include full
            formatting and can be printed or shared.
          </p>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => handleGenerateReport('html')}
              disabled={generatingReport}
            >
              Generate HTML
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => handleGenerateReport('json')}
              disabled={generatingReport}
            >
              Generate JSON
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
