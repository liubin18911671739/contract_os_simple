/**
 * Metrics Comparison Component
 * Displays comparison between current period and baseline (previous period)
 */

import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { getBaselineComparison, BaselineComparison } from '../../api/metrics';

interface MetricsComparisonProps {
  from: string;
  to: string;
}

type PeriodType = 'week' | 'month' | 'custom';

export function MetricsComparison({ from, to }: MetricsComparisonProps) {
  const [data, setData] = useState<BaselineComparison | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [from, to]);

  async function loadData() {
    setLoading(true);
    try {
      const result = await getBaselineComparison(from, to);
      setData(result);
    } catch (error) {
      console.error('Failed to load baseline comparison:', error);
    } finally {
      setLoading(false);
    }
  }

  const getTrendIcon = (change: number) => {
    if (Math.abs(change) < 0.1) return <Minus className="w-4 h-4 text-gray-400" />;
    if (change > 0) return <TrendingUp className="w-4 h-4 text-emerald-500" />;
    return <TrendingDown className="w-4 h-4 text-red-500" />;
  };

  const getTrendColor = (change: number) => {
    if (Math.abs(change) < 0.1) return 'text-gray-400';
    return change > 0 ? 'text-emerald-500' : 'text-red-500';
  };

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

  // Prepare comparison chart data
  const comparisonData = [
    {
      metric: 'F1分数',
      当前: data.current_f1,
      基线: data.baseline_f1,
    },
    {
      metric: '精确度',
      当前: data.current_precision,
      基线: data.baseline_precision,
    },
    {
      metric: '召回率',
      当前: data.current_recall,
      基线: data.baseline_recall,
    },
    {
      metric: '幻觉率',
      当前: data.current_hallucination,
      基线: data.baseline_hallucination,
    },
  ];

  return (
    <div className="space-y-4">
      {/* Period info */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>对比周期</span>
        <span>
          {data.current_period.start} ~ {data.current_period.end}
          <span className="mx-2">vs</span>
          {data.baseline_period.start} ~ {data.baseline_period.end}
        </span>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* F1 Score */}
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-xs text-gray-500 mb-1">F1分数</div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-gray-900">{data.current_f1}%</div>
              <div className="text-xs text-gray-400">基线: {data.baseline_f1}%</div>
            </div>
            <div className={`flex items-center gap-1 ${getTrendColor(data.f1_change)}`}>
              {getTrendIcon(data.f1_change)}
              <span className="text-sm font-medium">{Math.abs(data.f1_change)}%</span>
            </div>
          </div>
        </div>

        {/* Precision */}
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-xs text-gray-500 mb-1">精确度</div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-gray-900">{data.current_precision}%</div>
              <div className="text-xs text-gray-400">基线: {data.baseline_precision}%</div>
            </div>
            <div className={`flex items-center gap-1 ${getTrendColor(data.precision_change)}`}>
              {getTrendIcon(data.precision_change)}
              <span className="text-sm font-medium">{Math.abs(data.precision_change)}%</span>
            </div>
          </div>
        </div>

        {/* Recall */}
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-xs text-gray-500 mb-1">召回率</div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-gray-900">{data.current_recall}%</div>
              <div className="text-xs text-gray-400">基线: {data.baseline_recall}%</div>
            </div>
            <div className={`flex items-center gap-1 ${getTrendColor(data.recall_change)}`}>
              {getTrendIcon(data.recall_change)}
              <span className="text-sm font-medium">{Math.abs(data.recall_change)}%</span>
            </div>
          </div>
        </div>

        {/* Hallucination */}
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-xs text-gray-500 mb-1">幻觉率</div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-gray-900">{data.current_hallucination}%</div>
              <div className="text-xs text-gray-400">基线: {data.baseline_hallucination}%</div>
            </div>
            <div className={`flex items-center gap-1 ${getTrendColor(-data.hallucination_change)}`}>
              {getTrendIcon(-data.hallucination_change)}
              <span className="text-sm font-medium">{Math.abs(data.hallucination_change)}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Comparison Chart */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-4">指标对比图</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={comparisonData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis type="category" dataKey="metric" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              formatter={(value) => `${value}%`}
              contentStyle={{ fontSize: 12 }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="当前" fill="#3B82F6" name="当前周期" radius={[4, 4, 0, 0]} />
            <Bar dataKey="基线" fill="#9CA3AF" name="基线周期" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
