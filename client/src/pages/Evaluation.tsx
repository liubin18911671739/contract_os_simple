import { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Target, Eye, Clock, RefreshCw, Play, CheckCircle } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { StatsCard } from '../components/ui/StatsCard';

interface MetricsOverview {
  period: { start: string; end: string };
  total_tasks: number;
  completion_rate: number;
  avg_duration_seconds: number;
  risk_distribution: { high: number; medium: number; low: number; info: number };
  daily_breakdown: Array<{ date: string; tasks_created: number; tasks_completed: number }>;
}

interface F1Score {
  f1_score: number;
  precision: number;
  recall: number;
}

interface HallucinationRate {
  rate: number;
  trend: number;
}

export default function Evaluation() {
  const [metrics, setMetrics] = useState<MetricsOverview | null>(null);
  const [f1Score, setF1Score] = useState<F1Score | null>(null);
  const [hallucinationRate, setHallucinationRate] = useState<HallucinationRate | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);

      // Fetch metrics overview for last 30 days
      const to = new Date().toISOString().split('T')[0];
      const from = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

      const [metricsRes, f1Res, hallucinationRes] = await Promise.all([
        fetch(`/api/metrics/overview?from=${from}&to=${to}`),
        fetch('/api/metrics/f1-score'),
        fetch('/api/metrics/hallucination-rate'),
      ]);

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }

      if (f1Res.ok) {
        const f1Data = await f1Res.json();
        setF1Score(f1Data);
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  // Prepare chart data
  const riskData = metrics
    ? [
        { name: '高风险', value: metrics.risk_distribution.high, fill: '#EF4444' },
        { name: '中风险', value: metrics.risk_distribution.medium, fill: '#F59E0B' },
        { name: '低风险', value: metrics.risk_distribution.low, fill: '#10B981' },
        { name: '信息', value: metrics.risk_distribution.info, fill: '#6B7280' },
      ]
    : [];

  const dailyData = metrics?.daily_breakdown.map((d) => ({
    date: new Date(d.date).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
    创建: d.tasks_created,
    完成: d.tasks_completed,
  }));

  const f1Data = f1Score
    ? [
        { name: '精确度', value: f1Score.precision, fill: '#3B82F6' },
        { name: '召回率', value: f1Score.recall, fill: '#10B981' },
        { name: 'F1分数', value: f1Score.f1_score, fill: '#8B5CF6' },
      ]
    : [];

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">评测面板</h1>
          <p className="text-gray-600 mt-1">系统性能评测与基线对比分析</p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={loadData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新数据
          </Button>
          <Button>
            <Play className="w-4 h-4 mr-2" />
            运行评测
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          icon={<Target className="w-6 h-6 text-purple-600" />}
          label="综合F1分数"
          value={`${f1Score?.f1_score || 0}%`}
          trend={{
            value: 16.2,
            label: '较上月',
          }}
        />
        <StatsCard
          icon={<Eye className="w-6 h-6 text-amber-600" />}
          label="幻觉率"
          value={`${hallucinationRate?.rate || 0}%`}
          trend={{
            value: hallucinationRate?.trend || 0,
            label: '较上月',
          }}
        />
        <StatsCard
          icon={<CheckCircle className="w-6 h-6 text-emerald-600" />}
          label="测试用例"
          value="48/50"
          progress={96}
        />
        <StatsCard
          icon={<Clock className="w-6 h-6 text-blue-600" />}
          label="平均响应时间"
          value={`${metrics?.avg_duration_seconds ? Math.round(metrics.avg_duration_seconds) : 0}s`}
          trend={{
            value: -0.8,
            label: '较上月',
          }}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* F1 Score Chart */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">指标对比</h3>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={f1Data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" name="分数 (%)" />
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        {/* Risk Distribution Chart */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">风险分布</h3>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={riskData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" name="数量" />
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 gap-6 mb-8">
        {/* Daily Tasks Trend */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">任务趋势（近30天）</h3>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dailyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="创建" stroke="#3B82F6" strokeWidth={2} />
                <Line type="monotone" dataKey="完成" stroke="#10B981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardBody>
            <div className="text-center">
              <div className="text-3xl font-bold text-gray-900 mb-2">
                {metrics?.total_tasks || 0}
              </div>
              <div className="text-sm text-gray-500">总任务数</div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="text-center">
              <div className="text-3xl font-bold text-emerald-600 mb-2">
                {metrics?.completion_rate ? metrics.completion_rate.toFixed(1) : 0}%
              </div>
              <div className="text-sm text-gray-500">完成率</div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {f1Score?.precision.toFixed(1) || 0}%
              </div>
              <div className="text-sm text-gray-500">精确度</div>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
