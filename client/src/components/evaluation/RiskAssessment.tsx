/**
 * Risk Assessment Component
 * Displays detailed risk assessment statistics by level and type
 */

import { useState, useEffect } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Shield, CheckCircle, XCircle, Clock } from 'lucide-react';
import { getRiskAssessment, type RiskAssessment as RiskAssessmentData } from '../../api/metrics';

interface RiskAssessmentProps {
  from: string;
  to: string;
}

const RISK_LEVEL_COLORS: Record<string, string> = {
  HIGH: '#EF4444',
  MEDIUM: '#F59E0B',
  LOW: '#10B981',
  INFO: '#6B7280',
};

const RISK_LEVEL_LABELS: Record<string, string> = {
  HIGH: '高风险',
  MEDIUM: '中风险',
  LOW: '低风险',
  INFO: '信息',
};

const PIE_COLORS = ['#10B981', '#EF4444', '#F59E0B'];

export function RiskAssessment({ from, to }: RiskAssessmentProps) {
  const [data, setData] = useState<RiskAssessmentData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [from, to]);

  async function loadData() {
    setLoading(true);
    try {
      const result = await getRiskAssessment(from, to);
      setData(result);
    } catch (error) {
      console.error('Failed to load risk assessment:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">暂无数据</div>
      </div>
    );
  }

  // Prepare risk level data for chart
  const levelChartData = Object.entries(data.by_level)
    .filter(([_, stats]) => stats.total > 0)
    .map(([level, stats]) => ({
      name: RISK_LEVEL_LABELS[level] || level,
      已确认: stats.confirmed,
      已忽略: stats.dismissed,
      待审核: stats.pending,
    }));

  // Prepare confirmation pie data
  const confirmed = data.overall_confirmation_rate;
  const dismissed = 100 - confirmed;
  const pieData = [
    { name: '已确认', value: confirmed },
    { name: '已忽略', value: dismissed },
  ];

  // Prepare risk type data for bar chart
  const typeChartData = Object.entries(data.by_type)
    .slice(0, 10) // Show top 10 types
    .map(([type, count]) => ({
      name: type || '未分类',
      数量: count,
    }))
    .sort((a, b) => b.数量 - a.数量);

  return (
    <div className="space-y-4">
      {/* Overall stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-5 h-5 text-emerald-600" />
            <span className="text-sm font-medium text-gray-700">确认率</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{data.overall_confirmation_rate}%</div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-medium text-gray-700">准确率</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{data.overall_accuracy}%</div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-5 h-5 text-purple-600" />
            <span className="text-sm font-medium text-gray-700">待审核</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {Object.values(data.by_level).reduce((sum, stats) => sum + stats.pending, 0)}
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confirmation Rate Pie Chart */}
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-4">审核状态分布</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
                label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
              >
                <Cell key="confirmed" fill={PIE_COLORS[0]} />
                <Cell key="dismissed" fill={PIE_COLORS[1]} />
              </Pie>
              <Tooltip formatter={(value) => `${value}%`} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Type Distribution */}
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-4">风险类型分布 (Top 10)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={typeChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="category" dataKey="name" tick={{ fontSize: 11 }} angle={-45} textAnchor="end" height={60} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="数量" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* By Level Stats Table */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-4">各等级详细统计</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 px-3 text-gray-600 font-medium">风险等级</th>
                <th className="text-right py-2 px-3 text-gray-600 font-medium">总计</th>
                <th className="text-right py-2 px-3 text-gray-600 font-medium">已确认</th>
                <th className="text-right py-2 px-3 text-gray-600 font-medium">已忽略</th>
                <th className="text-right py-2 px-3 text-gray-600 font-medium">待审核</th>
                <th className="text-right py-2 px-3 text-gray-600 font-medium">确认率</th>
                <th className="text-right py-2 px-3 text-gray-600 font-medium">准确率</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.by_level).map(([level, stats]) => (
                <tr key={level} className="border-b border-gray-100 last:border-0">
                  <td className="py-2 px-3">
                    <span
                      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium"
                      style={{ backgroundColor: RISK_LEVEL_COLORS[level] + '20', color: RISK_LEVEL_COLORS[level] }}
                    >
                      {RISK_LEVEL_LABELS[level] || level}
                    </span>
                  </td>
                  <td className="text-right py-2 px-3 text-gray-900">{stats.total}</td>
                  <td className="text-right py-2 px-3 text-emerald-600">{stats.confirmed}</td>
                  <td className="text-right py-2 px-3 text-red-600">{stats.dismissed}</td>
                  <td className="text-right py-2 px-3 text-gray-500">{stats.pending}</td>
                  <td className="text-right py-2 px-3 text-gray-900">{stats.confirmation_rate}%</td>
                  <td className="text-right py-2 px-3 text-gray-900">{stats.accuracy_rate}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* By Level Stacked Bar Chart */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-4">各等级审核状态</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={levelChartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="已确认" stackId="stack" fill="#10B981" name="已确认" radius={[2, 2, 0, 0]} />
            <Bar dataKey="已忽略" stackId="stack" fill="#EF4444" name="已忽略" radius={[2, 2, 0, 0]} />
            <Bar dataKey="待审核" stackId="stack" fill="#F59E0B" name="待审核" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
