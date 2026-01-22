/**
 * System Settings Component
 * LLM provider and model configuration
 */

import { useState, useEffect } from 'react';
import { useSettings } from '../../contexts/SettingsContext';
import { DEFAULT_SETTINGS, MODEL_OPTIONS, PROVIDER_OPTIONS } from '../../types/settings';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

const CardHeader = ({ children }: { children: React.ReactNode }) => (
  <div className="mb-4">{children}</div>
);

const CardBody = ({ children }: { children: React.ReactNode }) => (
  <div>{children}</div>
);

export default function SystemSettings() {
  const { settings, updateSettings } = useSettings();
  const [formData, setFormData] = useState({
    provider: settings.llm.provider,
    chatModel: settings.llm.chatModel,
    embedModel: settings.llm.embedModel,
    rerankModel: settings.llm.rerankModel,
    chatBaseUrl: settings.llm.chatBaseUrl || '',
    embedBaseUrl: settings.llm.embedBaseUrl || '',
    rerankBaseUrl: settings.llm.rerankBaseUrl || '',
    apiKey: settings.llm.apiKey || ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Update form data when settings change
  useEffect(() => {
    setFormData({
      provider: settings.llm.provider,
      chatModel: settings.llm.chatModel,
      embedModel: settings.llm.embedModel,
      rerankModel: settings.llm.rerankModel,
      chatBaseUrl: settings.llm.chatBaseUrl || '',
      embedBaseUrl: settings.llm.embedBaseUrl || '',
      rerankBaseUrl: settings.llm.rerankBaseUrl || '',
      apiKey: settings.llm.apiKey || ''
    });
  }, [settings.llm]);

  const handleProviderChange = (newProvider: 'local' | 'zhipu') => {
    if (newProvider !== formData.provider) {
      const providerName = newProvider === 'local' ? '本地 vLLM' : '智谱 Qingyan';
      if (confirm(`切换到 ${providerName} 将清空当前配置，确认继续？`)) {
        setFormData({
          ...formData,
          provider: newProvider,
          chatModel: DEFAULT_SETTINGS.llm.chatModel,
          embedModel: DEFAULT_SETTINGS.llm.embedModel,
          rerankModel: DEFAULT_SETTINGS.llm.rerankModel,
          chatBaseUrl: '',
          embedBaseUrl: '',
          rerankBaseUrl: '',
          apiKey: ''
        });
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (formData.provider === 'local') {
      if (!formData.chatBaseUrl.trim()) {
        setMessage({ type: 'error', text: '请输入 Chat 端点地址' });
        return;
      }
      if (!formData.embedBaseUrl.trim()) {
        setMessage({ type: 'error', text: '请输入 Embed 端点地址' });
        return;
      }
      if (!formData.rerankBaseUrl.trim()) {
        setMessage({ type: 'error', text: '请输入 Rerank 端点地址' });
        return;
      }
    } else {
      if (!formData.apiKey.trim()) {
        setMessage({ type: 'error', text: '请输入 API 密钥' });
        return;
      }
    }

    setLoading(true);
    setMessage(null);

    try {
      updateSettings({
        llm: {
          provider: formData.provider,
          chatModel: formData.chatModel,
          embedModel: formData.embedModel,
          rerankModel: formData.rerankModel,
          chatBaseUrl: formData.chatBaseUrl || undefined,
          embedBaseUrl: formData.embedBaseUrl || undefined,
          rerankBaseUrl: formData.rerankBaseUrl || undefined,
          apiKey: formData.apiKey || undefined
        }
      });

      setMessage({ type: 'success', text: '系统配置已保存' });
    } catch (error) {
      setMessage({ type: 'error', text: '保存失败，请重试' });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    if (confirm('确认重置为默认配置？')) {
      setFormData({
        provider: DEFAULT_SETTINGS.llm.provider,
        chatModel: DEFAULT_SETTINGS.llm.chatModel,
        embedModel: DEFAULT_SETTINGS.llm.embedModel,
        rerankModel: DEFAULT_SETTINGS.llm.rerankModel,
        chatBaseUrl: '',
        embedBaseUrl: '',
        rerankBaseUrl: '',
        apiKey: ''
      });
      setMessage(null);
    }
  };

  const currentProviderOptions = MODEL_OPTIONS[formData.provider];

  return (
    <div className="space-y-6">
      {/* LLM Provider Selection */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">LLM 提供商</h3>
          <p className="text-sm text-gray-500 mt-1">选择大模型服务提供商</p>
        </CardHeader>
        <CardBody>
          <div className="space-y-3">
            {PROVIDER_OPTIONS.map((option) => (
              <label
                key={option.value}
                className={`
                  flex items-center p-4 border-2 rounded-lg cursor-pointer transition-all
                  ${
                    formData.provider === option.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }
                `}
              >
                <input
                  type="radio"
                  name="provider"
                  value={option.value}
                  checked={formData.provider === option.value}
                  onChange={(e) => handleProviderChange(e.target.value as 'local' | 'zhipu')}
                  className="mr-3"
                />
                <div>
                  <div className="font-medium text-gray-900">{option.label}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {option.value === 'local'
                      ? '使用本地 vLLM 实例，需要配置三个独立的模型服务'
                      : '使用智谱 Qingyan 云服务，需要 API 密钥'}
                  </div>
                </div>
              </label>
            ))}
          </div>
        </CardBody>
      </Card>

      {/* Model Configuration */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">模型配置</h3>
          <p className="text-sm text-gray-500 mt-1">配置对话、嵌入和重排序模型</p>
        </CardHeader>
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Chat Model */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Chat 模型 *
              </label>
              <select
                value={formData.chatModel}
                onChange={(e) => setFormData({ ...formData, chatModel: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                {currentProviderOptions.chat.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                用于风险分析和合同审查的对话模型
              </p>
            </div>

            {/* Embed Model */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Embed 模型 *
              </label>
              <select
                value={formData.embedModel}
                onChange={(e) => setFormData({ ...formData, embedModel: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                {currentProviderOptions.embed.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                用于文本向量化的嵌入模型
              </p>
            </div>

            {/* Rerank Model */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Rerank 模型 *
              </label>
              <select
                value={formData.rerankModel}
                onChange={(e) => setFormData({ ...formData, rerankModel: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                {currentProviderOptions.rerank.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                用于检索结果重排序的模型
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

      {/* API Configuration */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">
            {formData.provider === 'local' ? '服务端点' : 'API 配置'}
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            {formData.provider === 'local'
              ? '配置本地 vLLM 服务端点'
              : '配置智谱 API 密钥'}
          </p>
        </CardHeader>
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-4">
            {formData.provider === 'local' ? (
              <>
                {/* Chat Base URL */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Chat 端点 *
                  </label>
                  <input
                    type="url"
                    value={formData.chatBaseUrl}
                    onChange={(e) => setFormData({ ...formData, chatBaseUrl: e.target.value })}
                    placeholder="http://localhost:8000/v1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    vLLM Chat 兼容的 API 端点地址
                  </p>
                </div>

                {/* Embed Base URL */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Embed 端点 *
                  </label>
                  <input
                    type="url"
                    value={formData.embedBaseUrl}
                    onChange={(e) => setFormData({ ...formData, embedBaseUrl: e.target.value })}
                    placeholder="http://localhost:8001/v1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    vLLM Embed 兼容的 API 端点地址
                  </p>
                </div>

                {/* Rerank Base URL */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Rerank 端点 *
                  </label>
                  <input
                    type="url"
                    value={formData.rerankBaseUrl}
                    onChange={(e) => setFormData({ ...formData, rerankBaseUrl: e.target.value })}
                    placeholder="http://localhost:8002/v1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    vLLM Rerank 兼容的 API 端点地址
                  </p>
                </div>
              </>
            ) : (
              <>
                {/* API Key */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    API 密钥 *
                  </label>
                  <input
                    type="password"
                    value={formData.apiKey}
                    onChange={(e) => setFormData({ ...formData, apiKey: e.target.value })}
                    placeholder="请输入智谱 API 密钥"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    从{' '}
                    <a
                      href="https://open.bigmodel.cn/usercenter/apikeys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      智谱开放平台
                    </a>{' '}
                    获取 API 密钥
                  </p>
                </div>

                {/* Base URLs (Optional) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Chat 基础 URL（可选）
                  </label>
                  <input
                    type="url"
                    value={formData.chatBaseUrl}
                    onChange={(e) => setFormData({ ...formData, chatBaseUrl: e.target.value })}
                    placeholder="https://open.bigmodel.cn/api/paas/v4"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    默认使用智谱官方端点，一般无需修改
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Embed 基础 URL（可选）
                  </label>
                  <input
                    type="url"
                    value={formData.embedBaseUrl}
                    onChange={(e) => setFormData({ ...formData, embedBaseUrl: e.target.value })}
                    placeholder="https://open.bigmodel.cn/api/paas/v4"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Rerank 基础 URL（可选）
                  </label>
                  <input
                    type="url"
                    value={formData.rerankBaseUrl}
                    onChange={(e) => setFormData({ ...formData, rerankBaseUrl: e.target.value })}
                    placeholder="https://open.bigmodel.cn/api/paas/v4"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </>
            )}

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
    </div>
  );
}
