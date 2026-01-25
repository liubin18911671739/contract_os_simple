import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Target, Eye, Clock, RefreshCw, CheckCircle } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { StatsCard } from '../components/ui/StatsCard';
import { RiskAssessment } from '../components/evaluation/RiskAssessment';

interface MetricsOverview {
  period: { start: string; end: string };
  total_tasks: number;
  completion_rate: number;
  avg_duration_seconds: number;
  risk_distribution: { high: number; medium: number; low: number; info: number };
  daily_breakdown: Array<{ date: string; tasks_created: number; tasks_completed: number }>;
}

interface HallucinationRate {
  rate: number;
  trend: number;
}

type PeriodType = 'week' | 'month';

export default function Evaluation() {
  const [periodType, setPeriodType] = useState<PeriodType>('month');
  const [metrics, setMetrics] = useState<MetricsOverview | null>(null);
  const [hallucinationRate, setHallucinationRate] = useState<HallucinationRate | null>(null);
  const [loading, setLoading] = useState(true);

  // Calculate date range based on period type
  const getDateRange = () => {
    const now = new Date();
    const to = now.toISOString().split('T')[0];
    let from: string;

    if (periodType === 'week') {
      // Last 7 days
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      from = weekAgo.toISOString().split('T')[0];
    } else {
      // Last 30 days (default)
      const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      from = monthAgo.toISOString().split('T')[0];
    }

    return { from, to };
  };

  useEffect(() => {
    loadData();
  }, [periodType]);

  async function loadData() {
    try {
      setLoading(true);
      const { from, to } = getDateRange();

      const [metricsRes, hallucinationRes] = await Promise.all([
        fetch(`/api/metrics/overview?from=${from}&to=${to}`),
        fetch('/api/metrics/hallucination-rate'),
      ]);

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }

      if (hallucinationRes.ok) {
        const hallucinationData = await hallucinationRes.json();
        setHallucinationRate(hallucinationData);
      }
    } catch (error) {
      console.error('Failed to fetch evaluation data:', error);
    } finally {
      setLoading(false);
    }
  }

  const { from, to } = getDateRange();

  const dailyData = metrics?.daily_breakdown.map((d) => ({
    date: new Date(d.date).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
    创建: d.tasks_created,
    完成: d.tasks_completed,
  }));

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">评测面板</h1>
          <p className="text-gray-600 mt-1">系统性能评测与基线对比分析</p>
        </div>
        <div className="flex gap-3">
          {/* Period Selector */}
          <div className="flex items-center bg-white rounded-lg border border-gray-200">
            <button
              onClick={() => setPeriodType('week')}
              className={`px-4 py-2 text-sm ${
                periodType === 'week'
                  ? 'bg-accent text-white'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              本周
            </button>
            <button
              onClick={() => setPeriodType('month')}
              className={`px-4 py-2 text-sm border-l ${
                periodType === 'month'
                  ? 'bg-accent text-white'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              本月
            </button>
          </div>
          <Button variant="secondary" onClick={loadData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新数据
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          icon={<Target className="w-6 h-6 text-purple-600" />}
          label="综合F1分数"
          value="--"
        />
        <StatsCard
          icon={<Eye className="w-6 h-6 text-amber-600" />}
          label="幻觉率"
          value={`${hallucinationRate?.rate || 0}%`}
        />
        <StatsCard
          icon={<CheckCircle className="w-6 h-6 text-emerald-600" />}
          label="总任务数"
          value={metrics?.total_tasks || 0}
        />
        <StatsCard
          icon={<Clock className="w-6 h-6 text-blue-600" />}
          label="平均响应时间"
          value={`${metrics?.avg_duration_seconds ? Math.round(metrics.avg_duration_seconds) : 0}s`}
        />
      </div>

      {/* Risk Assessment - Full Width */}
      <Card className="mb-8">
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">风险评估</h3>
          <p className="text-sm text-gray-500">风险等级分布与审核统计</p>
        </CardHeader>
        <CardBody>
          <RiskAssessment from={from} to={to} />
        </CardBody>
      </Card>

      {/* Task Trend Chart */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">任务趋势</h3>
          <p className="text-sm text-gray-500">每日任务创建与完成情况</p>
        </CardHeader>
        <CardBody>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="创建" stroke="#3B82F6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="完成" stroke="#10B981" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>
    </div>
  );
}
