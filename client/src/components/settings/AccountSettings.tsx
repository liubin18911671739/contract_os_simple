/**
 * Account Settings Component
 * User profile management
 */

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { useSettings } from '../../contexts/SettingsContext';
import { DEPARTMENT_OPTIONS } from '../../types/settings';

export default function AccountSettings() {
  const { settings, updateSettings } = useSettings();
  const [formData, setFormData] = useState({
    name: settings.user.name,
    department: settings.user.department,
    email: settings.user.email || ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Update form when settings change
  useEffect(() => {
    setFormData({
      name: settings.user.name,
      department: settings.user.department,
      email: settings.user.email || ''
    });
  }, [settings.user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formData.name.trim()) {
      setMessage({ type: 'error', text: '请输入姓名' });
      return;
    }

    if (formData.name.trim().length < 2) {
      setMessage({ type: 'error', text: '姓名至少需要 2 个字符' });
      return;
    }

    if (!formData.department) {
      setMessage({ type: 'error', text: '请选择部门' });
      return;
    }

    if (formData.email && !isValidEmail(formData.email)) {
      setMessage({ type: 'error', text: '请输入有效的邮箱地址' });
      return;
    }

    setLoading(true);
    try {
      updateSettings({
        user: {
          ...settings.user,
          name: formData.name.trim(),
          department: formData.department,
          email: formData.email || undefined
        }
      });
      setMessage({ type: 'success', text: '个人资料已保存' });
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: '保存失败，请重试' });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      name: settings.user.name,
      department: settings.user.department,
      email: settings.user.email || ''
    });
    setMessage(null);
  };

  return (
    <Card>
      <CardHeader>
        <h3 className="text-lg font-semibold">个人资料</h3>
        <p className="text-sm text-gray-500">管理您的个人信息</p>
      </CardHeader>
      <CardBody>
        {message && (
          <div className={`mb-4 p-4 rounded ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800'
              : 'bg-red-50 text-red-800'
          }`}>
            {message.text}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
             姓名 *
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="请输入您的姓名"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              部门 *
            </label>
            <Select
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              disabled={loading}
            >
              <option value="">请选择部门</option>
              {DEPARTMENT_OPTIONS.map((dept) => (
                <option key={dept.value} value={dept.value}>
                  {dept.label}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              邮箱
            </label>
            <Input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="your@email.com"
              disabled={loading}
            />
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={handleReset}
              disabled={loading}
            >
              重置
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? '保存中...' : '保存更改'}
            </Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}

function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}
