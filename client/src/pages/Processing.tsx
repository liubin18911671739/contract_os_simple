import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle, Loader, Clock, AlertCircle, XCircle, Users, Search, Brain, Shield } from 'lucide-react';
import { getTask, getTaskEvents } from '../api/tasks';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { ProgressBar } from '../components/ui/Progress';
import { Badge } from '../components/ui/Badge';

const STAGES = [
  'QUEUED',
  'PARSING',
  'STRUCTURING',
  'RULE_SCORING',
  'KB_RETRIEVAL',
  'LLM_RISK',
  'EVIDENCING',
  'QCING',
  'DONE',
];

const STAGE_LABELS: Record<string, string> = {
  QUEUED: '队列中',
  PARSING: '解析中',
  STRUCTURING: '结构化',
  RULE_SCORING: '规则评分',
  KB_RETRIEVAL: '知识库检索',
  LLM_RISK: 'AI风险分析',
  EVIDENCING: '证据收集',
  QCING: '质量检查',
  DONE: '完成',
};

const AGENTS = [
  {
    id: 'orchestrator',
    name: '协调Agent',
    icon: Users,
    description: '统筹协调整个分析流程，确保各Agent有序工作',
    stages: ['QUEUED', 'PARSING', 'STRUCTURING'],
  },
  {
    id: 'retriever',
    name: '检索Agent',
    icon: Search,
    description: '从知识库中检索相关法规、案例和先例',
    stages: ['KB_RETRIEVAL', 'RULE_SCORING'],
  },
  {
    id: 'analyst',
    name: '分析Agent',
    icon: Brain,
    description: '基于检索结果进行深度法律风险分析',
    stages: ['LLM_RISK', 'EVIDENCING'],
  },
  {
    id: 'qc',
    name: '质检Agent',
    icon: Shield,
    description: '质量检查和幻觉检测，确保分析准确性',
    stages: ['QCING', 'DONE'],
  },
];

export default function Processing() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [task, setTask] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [polling, setPolling] = useState(true);

  useEffect(() => {
    if (!taskId) return;

    const load = async () => {
      try {
        const [taskData, eventsData] = await Promise.all([getTask(taskId), getTaskEvents(taskId)]);
        setTask(taskData);
        setEvents(eventsData);

        if (
          taskData.status === 'DONE' ||
          taskData.status === 'FAILED' ||
          taskData.status === 'CANCELLED'
        ) {
          setPolling(false);
          if (taskData.status === 'DONE') {
            setTimeout(() => navigate(`/results/${taskId}`), 2000);
          }
        }
      } catch (error) {
        console.error('Failed to load task:', error);
      }
    };

    load();
    const interval = polling ? setInterval(load, 2000) : undefined;
    return () => clearInterval(interval);
  }, [taskId, polling, navigate]);

  if (!task) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  const getAgentStatus = (agent: typeof AGENTS[0]) => {
    const currentStageIndex = STAGES.indexOf(task.current_stage);
    const agentStageIndex = Math.max(...agent.stages.map((s) => STAGES.indexOf(s)));

    if (task.status === 'FAILED' && agent.stages.includes(task.current_stage)) {
      return 'error';
    }
    if (task.status === 'DONE' || currentStageIndex > agentStageIndex) {
      return 'completed';
    }
    if (agent.stages.includes(task.current_stage)) {
      return 'active';
    }
    return 'pending';
  };

  const renderAgentIcon = (agent: typeof AGENTS[0]) => {
    const status = getAgentStatus(agent);

    if (status === 'completed') {
      return (
        <div className="p-3 bg-emerald-50 rounded-lg">
          <CheckCircle className="w-6 h-6 text-emerald-600" />
        </div>
      );
    }
    if (status === 'active') {
      return (
        <div className="p-3 bg-blue-50 rounded-lg">
          <Loader className="w-6 h-6 text-accent animate-spin" />
        </div>
      );
    }
    if (status === 'error') {
      return (
        <div className="p-3 bg-red-50 rounded-lg">
          <XCircle className="w-6 h-6 text-red-600" />
        </div>
      );
    }
    return (
      <div className="p-3 bg-gray-50 rounded-lg">
        <Clock className="w-6 h-6 text-gray-400" />
      </div>
    );
  };

  const renderAgentCard = (agent: typeof AGENTS[0]) => {
    const status = getAgentStatus(agent);

    return (
      <Card
        key={agent.id}
        className={`transition-all ${
          status === 'active'
            ? 'ring-2 ring-accent shadow-lg'
            : status === 'completed'
            ? 'opacity-75'
            : 'opacity-50'
        }`}
      >
        <CardBody>
          <div className="flex items-start gap-4">
            {renderAgentIcon(agent)}
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-gray-900">{agent.name}</h4>
                <Badge
                  color={
                    status === 'completed'
                      ? 'emerald'
                      : status === 'active'
                      ? 'blue'
                      : status === 'error'
                      ? 'red'
                      : 'gray'
                  }
                >
                  {status === 'completed'
                    ? '已完成'
                    : status === 'active'
                    ? '进行中'
                    : status === 'error'
                    ? '失败'
                    : '等待中'}
                </Badge>
              </div>
              <p className="text-sm text-gray-600">{agent.description}</p>
              {status === 'active' && (
                <div className="mt-3">
                  <ProgressBar progress={task.progress} />
                </div>
              )}
            </div>
          </div>
        </CardBody>
      </Card>
    );
  };

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">分析任务</h1>
          <p className="text-gray-600 mt-1">
            任务ID: <span className="font-mono text-sm">{taskId}</span>
          </p>
        </div>
        <Button variant="secondary" onClick={() => navigate('/')}>
          返回控制台
        </Button>
      </div>

      {/* Overall Progress */}
      <Card className="mb-8">
        <CardBody>
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-semibold text-gray-900">总体进度</h3>
            <div className="flex items-center gap-2">
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
                  : task.status === 'CANCELLED'
                  ? '已取消'
                  : STAGE_LABELS[task.current_stage] || task.current_stage}
              </Badge>
              <span className="text-sm font-medium text-gray-700">{task.progress}%</span>
            </div>
          </div>
          <ProgressBar progress={task.progress} />
          <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
            <span>开始时间: {new Date(task.created_at).toLocaleString('zh-CN')}</span>
            {task.status === 'DONE' && (
              <span>完成时间: {new Date(task.updated_at).toLocaleString('zh-CN')}</span>
            )}
          </div>
        </CardBody>
      </Card>

      {/* Agent Cards */}
      <div className="space-y-4 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Agent工作流</h2>
        {AGENTS.map(renderAgentCard)}
      </div>

      {/* Error Message */}
      {task.error_message && (
        <Card className="border-l-4 border-l-red-500 mb-8">
          <CardBody>
            <div className="flex items-start gap-3">
              <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-red-900 mb-1">分析失败</h4>
                <p className="text-sm text-red-700">{task.error_message}</p>
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Activity Log */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">活动日志</h3>
        </CardHeader>
        <CardBody>
          <div className="space-y-3">
            {events.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">暂无日志</p>
            ) : (
              events.map((event) => (
                <div key={event.id} className="flex items-start gap-3 text-sm">
                  <div className="flex-shrink-0 w-2 h-2 mt-2 rounded-full bg-accent" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900">{STAGE_LABELS[event.stage] || event.stage}</span>
                      <span className="text-xs text-gray-500">
                        {new Date(event.ts).toLocaleTimeString('zh-CN')}
                      </span>
                    </div>
                    <p className="text-gray-600 mt-1">{event.message}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardBody>
      </Card>

      {/* Navigation to Results */}
      {task.status === 'DONE' && (
        <div className="mt-8 text-center">
          <p className="text-gray-600 mb-4">分析完成！正在跳转到结果页面...</p>
          <Button onClick={() => navigate(`/results/${taskId}`)}>查看结果</Button>
        </div>
      )}
    </div>
  );
}
