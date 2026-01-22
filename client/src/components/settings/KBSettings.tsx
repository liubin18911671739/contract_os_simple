/**
 * Knowledge Base Settings Component
 * Chunking and retrieval parameters configuration
 */

import { useState, useEffect } from 'react';
import { useSettings } from '../../contexts/SettingsContext';
import { DEFAULT_SETTINGS } from '../../types/settings';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

const CardHeader = ({ children }: { children: React.ReactNode }) => (
  <div className="mb-4">{children}</div>
);

const CardBody = ({ children }: { children: React.ReactNode }) => (
  <div>{children}</div>
);

export default function KBSettings() {
  const { settings, updateSettings } = useSettings();
  const [formData, setFormData] = useState({
    chunkSize: settings.kb.chunkSize,
    chunkOverlap: settings.kb.chunkOverlap,
    topK: settings.kb.topK,
    topN: settings.kb.topN
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Update form data when settings change
  useEffect(() => {
    setFormData({
      chunkSize: settings.kb.chunkSize,
      chunkOverlap: settings.kb.chunkOverlap,
      topK: settings.kb.topK,
      topN: settings.kb.topN
    });
  }, [settings.kb]);

  const validateSettings = (): string[] => {
    const errors: string[] = [];

    // Validate chunk size vs overlap
    if (formData.chunkSize <= formData.chunkOverlap) {
      errors.push('分块大小必须大于重叠大小');
    }

    // Validate chunk size range
    if (formData.chunkSize < 100 || formData.chunkSize > 5000) {
      errors.push('分块大小必须在 100-5000 之间');
    }

    // Validate chunk overlap range
    if (formData.chunkOverlap < 0 || formData.chunkOverlap > 1000) {
      errors.push('分块重叠必须在 0-1000 之间');
    }

    // Validate topK vs topN
    if (formData.topK < formData.topN) {
      errors.push('Top-K 必须大于或等于 Top-N');
    }

    // Validate topK range
    if (formData.topK < 5 || formData.topK > 100) {
      errors.push('Top-K 必须在 5-100 之间');
    }

    // Validate topN range
    if (formData.topN < 3 || formData.topN > 20) {
      errors.push('Top-N 必须在 3-20 之间');
    }

    return errors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate settings
    const errors = validateSettings();
    if (errors.length > 0) {
      setMessage({ type: 'error', text: errors.join('; ') });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      updateSettings({
        kb: {
          chunkSize: formData.chunkSize,
          chunkOverlap: formData.chunkOverlap,
          topK: formData.topK,
          topN: formData.topN
        }
      });

      setMessage({ type: 'success', text: '知识库配置已保存' });
    } catch (error) {
      setMessage({ type: 'error', text: '保存失败，请重试' });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    if (confirm('确认重置为默认配置？')) {
      setFormData({
        chunkSize: DEFAULT_SETTINGS.kb.chunkSize,
        chunkOverlap: DEFAULT_SETTINGS.kb.chunkOverlap,
        topK: DEFAULT_SETTINGS.kb.topK,
        topN: DEFAULT_SETTINGS.kb.topN
      });
      setMessage(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Chunking Settings */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">文本分块配置</h3>
          <p className="text-sm text-gray-500 mt-1">
            配置文档文本分块的大小和重叠参数
          </p>
        </CardHeader>
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Chunk Size */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                分块大小 (Chunk Size) *
              </label>
              <input
                type="number"
                min={100}
                max={5000}
                step={50}
                value={formData.chunkSize}
                onChange={(e) =>
                  setFormData({ ...formData, chunkSize: parseInt(e.target.value) || 0 })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                文本分块的最大字符数。较大的值会产生更大的块，但可能降低检索精度。
                推荐值：1000-1500
              </p>
            </div>

            {/* Chunk Overlap */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                分块重叠 (Chunk Overlap) *
              </label>
              <input
                type="number"
                min={0}
                max={1000}
                step={50}
                value={formData.chunkOverlap}
                onChange={(e) =>
                  setFormData({ ...formData, chunkOverlap: parseInt(e.target.value) || 0 })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                相邻分块之间的重叠字符数，用于保留上下文连贯性。推荐值：150-250
              </p>
            </div>

            {/* Message Display */}
            {message && (
              <div
                className={`p-3 rounded-md ${
                  message.type === 'success'
                    ? 'bg-green-50 text-green-800 border border-green-200'
                    : 'bg-red-50 text-red-800 border border-red-200'
                }`}
              >
                {message.text}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end space-x-2 pt-4 border-t">
              <Button type="button" variant="secondary" onClick={handleReset}>
                重置为默认
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? '保存中...' : '保存更改'}
              </Button>
            </div>
          </form>
        </CardBody>
      </Card>

      {/* Retrieval Settings */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">检索配置</h3>
          <p className="text-sm text-gray-500 mt-1">
            配置向量检索和重排序参数
          </p>
        </CardHeader>
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Top-K */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                检索 Top-K *
              </label>
              <input
                type="number"
                min={5}
                max={100}
                step={5}
                value={formData.topK}
                onChange={(e) =>
                  setFormData({ ...formData, topK: parseInt(e.target.value) || 0 })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                向量检索返回的最大块数。较大的值会提高召回率，但增加处理时间。
                推荐值：15-25
              </p>
            </div>

            {/* Top-N */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                重排序 Top-N *
              </label>
              <input
                type="number"
                min={3}
                max={20}
                step={1}
                value={formData.topN}
                onChange={(e) =>
                  setFormData({ ...formData, topN: parseInt(e.target.value) || 0 })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                从 Top-K 个结果中重排序选出的最终块数。应该小于 Top-K。
                推荐值：5-8
              </p>
            </div>

            {/* Message Display */}
            {message && (
              <div
                className={`p-3 rounded-md ${
                  message.type === 'success'
                    ? 'bg-green-50 text-green-800 border border-green-200'
                    : 'bg-red-50 text-red-800 border border-red-200'
                }`}
              >
                {message.text}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end space-x-2 pt-4 border-t">
              <Button type="button" variant="secondary" onClick={handleReset}>
                重置为默认
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? '保存中...' : '保存更改'}
              </Button>
            </div>
          </form>
        </CardBody>
      </Card>

      {/* Performance Tips */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">性能优化建议</h3>
        </CardHeader>
        <CardBody>
          <div className="space-y-3 text-sm text-gray-700">
            <div>
              <strong className="text-gray-900">提高检索精度：</strong>
              <p className="mt-1">
                • 减少 chunkSize（如 800-1000）可以提高精度，但会增加块数量
              </p>
              <p>• 增加 chunkOverlap（如 250-300）可以保留更多上下文</p>
            </div>

            <div>
              <strong className="text-gray-900">提高检索速度：</strong>
              <p className="mt-1">
                • 减少 topK（如 15-20）可以减少向量检索时间
              </p>
              <p>• 减少 topN（如 5-6）可以减少重排序计算量</p>
            </div>

            <div>
              <strong className="text-gray-900">平衡配置：</strong>
              <p className="mt-1">
                • 默认配置（1000/200/20/6）适用于大多数场景
              </p>
              <p>
                • 对于长文档，可以增加 chunkSize（如 1500）和 topK（如 25）
              </p>
            </div>

            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <strong className="text-yellow-800">注意：</strong>
              <span className="text-yellow-700">
                {' '}
                修改这些配置不会影响已索引的知识库文档。新配置仅在重新索引或添加新文档时生效。
              </span>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
