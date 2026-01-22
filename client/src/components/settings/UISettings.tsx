/**
 * UI Settings Component
 * Language, theme, and notification preferences
 */

import { useState } from 'react';
import { useSettings } from '../../contexts/SettingsContext';
import { LANGUAGE_OPTIONS, THEME_OPTIONS } from '../../types/settings';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Toggle } from '../ui/Toggle';

const CardHeader = ({ children }: { children: React.ReactNode }) => (
  <div className="mb-4">{children}</div>
);

const CardBody = ({ children }: { children: React.ReactNode }) => (
  <div>{children}</div>
);

export default function UISettings() {
  const { settings, updateSettings } = useSettings();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      // Settings are already updated via the individual handlers
      setMessage({ type: 'success', text: '界面设置已保存' });
    } catch (error) {
      setMessage({ type: 'error', text: '保存失败，请重试' });
    } finally {
      setLoading(false);
    }
  };

  const handleLanguageChange = (language: 'zh-CN' | 'en-US') => {
    updateSettings({
      preferences: {
        ...settings.preferences,
        language
      }
    });
  };

  const handleThemeChange = (theme: 'light' | 'dark') => {
    updateSettings({
      preferences: {
        ...settings.preferences,
        theme
      }
    });
  };

  const handleNotificationsChange = (notifications: boolean) => {
    updateSettings({
      preferences: {
        ...settings.preferences,
        notifications
      }
    });
  };

  return (
    <div className="space-y-6">
      {/* Language Settings */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">语言设置</h3>
          <p className="text-sm text-gray-500 mt-1">选择界面显示语言</p>
        </CardHeader>
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                界面语言
              </label>
              <div className="flex space-x-4">
                {LANGUAGE_OPTIONS.map((option) => (
                  <label key={option.value} className="flex items-center">
                    <input
                      type="radio"
                      name="language"
                      value={option.value}
                      checked={settings.preferences.language === option.value}
                      onChange={() => handleLanguageChange(option.value as 'zh-CN' | 'en-US')}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                    <span className="text-sm text-gray-700">{option.label}</span>
                  </label>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                注意：更改语言后需要刷新页面才能完全生效
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
          </form>
        </CardBody>
      </Card>

      {/* Theme Settings */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">主题设置</h3>
          <p className="text-sm text-gray-500 mt-1">选择界面主题（当前仅支持浅色主题）</p>
        </CardHeader>
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                主题模式
              </label>
              <div className="flex space-x-4">
                {THEME_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => handleThemeChange(option.value as 'light' | 'dark')}
                    disabled={option.value === 'dark'}
                    className={`
                      px-4 py-2 rounded-md border-2 transition-all
                      ${
                        settings.preferences.theme === option.value
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-300 text-gray-700 hover:border-gray-400'
                      }
                      ${option.value === 'dark' ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                <span className="inline-flex items-center">
                  <svg
                    className="w-4 h-4 mr-1 text-yellow-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                  深色主题功能正在开发中，敬请期待
                </span>
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
          </form>
        </CardBody>
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">通知设置</h3>
          <p className="text-sm text-gray-500 mt-1">管理系统通知和提醒</p>
        </CardHeader>
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900">启用通知</div>
                <div className="text-xs text-gray-500 mt-1">
                  接收任务完成、风险告警等系统通知
                </div>
              </div>
              <Toggle
                checked={settings.preferences.notifications}
                onChange={handleNotificationsChange}
                aria-label="启用通知"
              />
            </div>

            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-sm text-blue-800">
                <strong>通知功能说明：</strong>
                开启通知后，系统会在以下情况提醒您：
              </p>
              <ul className="text-xs text-blue-700 mt-2 space-y-1 list-disc list-inside">
                <li>合同分析任务完成</li>
                <li>发现高风险条款</li>
                <li>知识库文档索引完成</li>
                <li>系统更新和维护通知</li>
              </ul>
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
            <div className="flex justify-end pt-4 border-t">
              <Button type="submit" disabled={loading}>
                {loading ? '保存中...' : '确认更改'}
              </Button>
            </div>
          </form>
        </CardBody>
      </Card>

      {/* Preview Card */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">设置预览</h3>
        </CardHeader>
        <CardBody>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">当前语言</span>
              <span className="font-medium text-gray-900">
                {LANGUAGE_OPTIONS.find((opt) => opt.value === settings.preferences.language)?.label}
              </span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">当前主题</span>
              <span className="font-medium text-gray-900">
                {THEME_OPTIONS.find((opt) => opt.value === settings.preferences.theme)?.label}
              </span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">通知状态</span>
              <span className="font-medium text-gray-900">
                {settings.preferences.notifications ? '已启用' : '已禁用'}
              </span>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
