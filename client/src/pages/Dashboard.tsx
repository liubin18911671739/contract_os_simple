import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { Button } from '../components/ui/Button';
import {
  Table,
  TableHead,
  TableHeader,
  TableBody,
  TableRow,
  TableCell,
} from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { StatsCard } from '../components/ui/StatsCard';
import { ProgressBar } from '../components/ui/Progress';

interface DashboardStats {
  total_contracts: number;
  high_risk_findings: number;
  compliance_rate: number;
  avg_processing_time: number;
  trends_7d: {
    contracts_analyzed: number;
    risk_discovery: number;
    compliance_rate: number;
  };
}

interface RecentTask {
  id: string;
  contract_name: string;
  status: string;
  progress: number;
  created_at: string;
  high_risks: number;
  medium_risks: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [tasks, setTasks] = useState<RecentTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchData() {
      try {
        setError(null);

        // Fetch stats
        const statsRes = await fetch('/api/dashboard/stats');
        if (!isMounted) return;

        if (statsRes.ok) {
          const statsData = await statsRes.json();
          setStats(statsData);
        } else if (statsRes.status === 500) {
          setError('数据库服务不可用，请检查 Docker 服务是否运行');
          setLoading(false);
          return; // Stop early on error
        }

        // Only fetch tasks if stats succeeded
        const tasksRes = await fetch('/api/dashboard/recent-tasks?page=1&limit=5');
        if (!isMounted) return;

        if (tasksRes.ok) {
          const tasksData = await tasksRes.json();
          setTasks(tasksData.tasks || []);
        } else if (tasksRes.status === 500) {
          setError('数据库服务不可用，请检查 Docker 服务是否运行');
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to fetch dashboard data:', err);
          setError('网络连接失败，请检查后端服务是否运行');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">欢迎回来</h1>
          <p className="text-gray-600 mt-1">这是您的合同法律分析系统概览</p>
        </div>

        {/* Error Message */}
        <Card>
          <CardBody>
            <div className="text-center py-8">
              <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">服务暂不可用</h3>
              <p className="text-gray-600 mb-4">{error}</p>
              <div className="text-sm text-gray-500 space-y-2">
                <p>请运行以下命令启动数据库服务：</p>
                <code className="block bg-gray-100 px-4 py-2 rounded text-left">
                  npm run docker:up
                </code>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }

  return (
    <div>
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">欢迎回来</h1>
        <p className="text-gray-600 mt-1">这是您的合同法律分析系统概览</p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            icon={<FileText className="w-6 h-6 text-blue-600" />}
            label="本月审查"
            value={stats.total_contracts}
            trend={{
              value: stats.trends_7d.contracts_analyzed,
              label: '较上周',
            }}
          />
          <StatsCard
            icon={<AlertTriangle className="w-6 h-6 text-red-600" />}
            label="高风险发现"
            value={stats.high_risk_findings}
            trend={{
              value: stats.trends_7d.risk_discovery,
              label: '较上周',
            }}
          />
          <StatsCard
            icon={<CheckCircle className="w-6 h-6 text-emerald-600" />}
            label="合规通过率"
            value={`${stats.compliance_rate}%`}
            trend={{
              value: stats.trends_7d.compliance_rate,
              label: '较上周',
            }}
          />
          <StatsCard
            icon={<Clock className="w-6 h-6 text-purple-600" />}
            label="平均耗时"
            value={`${Math.round(stats.avg_processing_time / 60)}分`}
            trend={{
              value: 15.4,
              label: '较上周',
            }}
          />
        </div>
      )}

      {/* Recent Analysis */}
      <Card>
        <CardHeader className="flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900">最近分析</h2>
          <Link to="/processing">
            <Button variant="ghost" size="sm">
              查看全部
            </Button>
          </Link>
        </CardHeader>
        <CardBody>
          <Table>
            <TableHead>
              <TableHeader>合同名称</TableHeader>
              <TableHeader>状态</TableHeader>
              <TableHeader>进度</TableHeader>
              <TableHeader>风险</TableHeader>
              <TableHeader>创建时间</TableHeader>
              <TableHeader>操作</TableHeader>
            </TableHead>
            <TableBody>
              {tasks.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-gray-500 py-8">
                    暂无分析任务
                    <Link to="/new-task" className="ml-2 text-accent hover:underline">
                      创建第一个任务
                    </Link>
                  </TableCell>
                </TableRow>
              ) : (
                tasks.map((task) => (
                  <TableRow key={task.id}>
                    <TableCell className="font-medium">{task.contract_name}</TableCell>
                    <TableCell>
                      <Badge
                        color={
                          task.status === 'DONE'
                            ? 'emerald'
                            : task.status === 'FAILED'
                            ? 'red'
                            : 'blue'
                        }
                      >
                        {task.status === 'DONE'
                          ? '完成'
                          : task.status === 'FAILED'
                          ? '失败'
                          : '进行中'}
                      </Badge>
                    </TableCell>
                    <TableCell className="w-32">
                      <ProgressBar progress={task.progress} />
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        {task.high_risks > 0 && (
                          <span className="text-red-600 text-sm">高: {task.high_risks}</span>
                        )}
                        {task.medium_risks > 0 && (
                          <span className="text-amber-600 text-sm">中: {task.medium_risks}</span>
                        )}
                        {task.high_risks === 0 && task.medium_risks === 0 && (
                          <span className="text-gray-400 text-sm">无</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {new Date(task.created_at).toLocaleDateString('zh-CN')}
                    </TableCell>
                    <TableCell>
                      {task.status === 'DONE' ? (
                        <Link to={`/results/${task.id}`}>
                          <Button size="sm" variant="secondary">
                            查看结果
                          </Button>
                        </Link>
                      ) : (
                        <Link to={`/processing/${task.id}`}>
                          <Button size="sm" variant="ghost">
                            查看进度
                          </Button>
                        </Link>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
    </div>
  );
}
