/**
 * Suggestion Editor Component
 * Modal for editing suggestions with validation
 */

import { useState, useEffect } from 'react';
import { X, Save, RotateCcw } from 'lucide-react';
import { updateSuggestion } from '../../api/suggestions';

interface SuggestionEditorProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (suggestionId: string, newText: string) => void;
  suggestionId: string;
  initialText: string;
  riskSummary?: string;
  clauseText?: string;
}

export function SuggestionEditor({
  isOpen,
  onClose,
  onSave,
  suggestionId,
  initialText,
  riskSummary,
  clauseText,
}: SuggestionEditorProps) {
  const [text, setText] = useState(initialText);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setText(initialText);
    setHasChanges(false);
    setError(null);
  }, [initialText, isOpen]);

  const handleChange = (value: string) => {
    setText(value);
    setHasChanges(value !== initialText);
    setError(null);
  };

  const handleReset = () => {
    setText(initialText);
    setHasChanges(false);
    setError(null);
  };

  const handleSave = async () => {
    if (!text.trim()) {
      setError('建议内容不能为空');
      return;
    }

    if (text.length < 10) {
      setError('建议内容太短，请提供更详细的修改建议');
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      await updateSuggestion(suggestionId, text);
      onSave(suggestionId, text);
      onClose();
    } catch (err: any) {
      setError(err.message || '保存失败，请重试');
    } finally {
      setIsSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
    // Ctrl/Cmd + S to save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      handleSave();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" onKeyDown={handleKeyDown}>
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-black opacity-30"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">编辑修改建议</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500 transition-colors p-1"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Context info */}
          {(riskSummary || clauseText) && (
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              {riskSummary && (
                <div className="mb-2">
                  <span className="text-xs font-medium text-gray-500">风险摘要:</span>
                  <p className="text-sm text-gray-700">{riskSummary}</p>
                </div>
              )}
              {clauseText && (
                <div>
                  <span className="text-xs font-medium text-gray-500">条款原文:</span>
                  <p className="text-sm text-gray-600 font-mono line-clamp-2">{clauseText}</p>
                </div>
              )}
            </div>
          )}

          {/* Editor */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              修改建议 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={text}
              onChange={(e) => handleChange(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-accent focus:border-accent min-h-[200px] resize-y"
              placeholder="请输入具体的修改建议，例如：建议将该条款修改为..."
              disabled={isSaving}
            />
            <div className="flex justify-between mt-1">
              <span className="text-xs text-gray-500">
                {text.length} 字符
              </span>
              <span className="text-xs text-gray-500">
                提示: Ctrl+S 快速保存
              </span>
            </div>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-3">
            <button
              onClick={handleReset}
              disabled={isSaving || !hasChanges}
              className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              重置
            </button>
            <button
              onClick={onClose}
              disabled={isSaving}
              className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
            >
              取消
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || !hasChanges}
              className="px-4 py-2 text-sm bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  保存中...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  保存
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Suggestion Editor with Diff View
 * Shows before/after comparison for suggestion edits
 */

interface Revision {
  revision_no: number;
  suggestion_text: string;
  created_by: string | null;
  created_at: string;
}

interface SuggestionDiffViewerProps {
  isOpen: boolean;
  onClose: () => void;
  currentText: string;
  revisions: Revision[];
}

export function SuggestionDiffViewer({
  isOpen,
  onClose,
  currentText,
  revisions,
}: SuggestionDiffViewerProps) {
  if (!isOpen) return null;

  // Sort revisions by number (newest first)
  const sortedRevisions = [...revisions].sort((a, b) => b.revision_no - a.revision_no);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div
          className="fixed inset-0 bg-black opacity-30"
          onClick={onClose}
        />

        <div className="relative bg-white rounded-lg shadow-xl max-w-3xl w-full p-6 max-h-[80vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between mb-4 flex-shrink-0">
            <h3 className="text-lg font-medium text-gray-900">建议修订历史</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500 transition-colors p-1"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Scrollable content */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {/* Current version */}
            <div className="bg-purple-50 rounded-lg border border-purple-200 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-purple-900">
                  当前版本
                </span>
                <span className="text-xs text-purple-600">最新</span>
              </div>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{currentText}</p>
            </div>

            {/* Divider */}
            {sortedRevisions.length > 0 && (
              <div className="flex items-center gap-2">
                <div className="flex-1 h-px bg-gray-200" />
                <span className="text-xs text-gray-500">修订历史</span>
                <div className="flex-1 h-px bg-gray-200" />
              </div>
            )}

            {/* Revisions */}
            {sortedRevisions.map((revision) => (
              <div
                key={revision.revision_no}
                className="bg-gray-50 rounded-lg border border-gray-200 p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    修订 #{revision.revision_no}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(revision.created_at).toLocaleString('zh-CN')}
                  </span>
                </div>
                <div className="text-xs text-gray-500 mb-2">
                  创建者: {revision.created_by || '系统'}
                </div>
                <p className="text-sm text-gray-700 whitespace-pre-wrap font-mono bg-white p-2 rounded border">
                  {revision.suggestion_text}
                </p>
              </div>
            ))}

            {sortedRevisions.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <p>暂无修订历史</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
