import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  getTask,
  getTaskSummary,
  getTaskClauses,
  generateReport,
  getReportDownloadUrl,
} from '../api/tasks';
import { Button } from '../components/ui/Button';
import { RiskBadge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import {
  Table,
  TableHead,
  TableHeader,
  TableBody,
  TableRow,
  TableCell,
} from '../components/ui/Table';

export default function Results() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [task, setTask] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [clauses, setClauses] = useState<any[]>([]);
  const [filter, setFilter] = useState<string>('');
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportMessage, setReportMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  useEffect(() => {
    if (!taskId) return;
    load();
  }, [taskId, filter]);

  async function load() {
    try {
      const [taskData, summaryData, clausesData] = await Promise.all([
        getTask(taskId!),
        getTaskSummary(taskId!),
        getTaskClauses(taskId!, { risk_level: filter || undefined }),
      ]);
      setTask(taskData);
      setSummary(summaryData);
      setClauses(clausesData as any[]);
    } catch (error) {
      console.error('Failed to load results:', error);
    }
  }

  async function handleGenerateReport(format: 'html' | 'json') {
    setGeneratingReport(true);
    setReportMessage(null);

    try {
      const result: any = await generateReport(taskId!, format);

      // Show success message with download option
      setReportMessage({
        type: 'success',
        text: `Report generated successfully! Report ID: ${result.reportId}`,
      });

      // Auto-open download link after short delay
      setTimeout(async () => {
        const downloadUrl = await getReportDownloadUrl(result.reportId);
        window.open(downloadUrl, '_blank');
      }, 1000);
    } catch (error: any) {
      setReportMessage({
        type: 'error',
        text: `Failed to generate report: ${error.message || 'Unknown error'}`,
      });
    } finally {
      setGeneratingReport(false);
    }
  }

  if (!task || !summary) {
    return <div className="text-center py-12">Loading...</div>;
  }

  const isTaskComplete = task.status === 'DONE';

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Analysis Results</h2>
        <div className="flex gap-2">
          {isTaskComplete && (
            <>
              <Button
                variant="secondary"
                onClick={() => handleGenerateReport('html')}
                disabled={generatingReport}
              >
                {generatingReport ? 'Generating...' : '📄 HTML Report'}
              </Button>
              <Button onClick={() => handleGenerateReport('json')} disabled={generatingReport}>
                {generatingReport ? 'Generating...' : '📊 JSON Report'}
              </Button>
            </>
          )}
          <Button variant="ghost" onClick={() => navigate('/')}>
            Back to Dashboard
          </Button>
        </div>
      </div>

      {reportMessage && <Alert type={reportMessage.type}>{reportMessage.text}</Alert>}

      {!isTaskComplete && (
        <Alert type="info">
          Task is still in progress. Reports can be generated once analysis is complete. Current
          status: <strong>{task.status}</strong> ({task.progress}%)
        </Alert>
      )}

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500">High Risks</div>
          <div className="text-2xl font-bold text-red-600">{summary.high_risks || 0}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500">Medium Risks</div>
          <div className="text-2xl font-bold text-amber-600">{summary.medium_risks || 0}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500">Low Risks</div>
          <div className="text-2xl font-bold text-emerald-600">{summary.low_risks || 0}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500">Clauses</div>
          <div className="text-2xl font-bold text-gray-900">{summary.clause_count || 0}</div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">Risks by Clause</h3>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">All Levels</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
              <option value="INFO">Info</option>
            </select>
          </div>
        </div>

        <Table>
          <TableHead>
            <TableHeader>Clause</TableHeader>
            <TableHeader>Summary</TableHeader>
            <TableHeader>Risk Level</TableHeader>
            <TableHeader>Status</TableHeader>
            <TableHeader>Actions</TableHeader>
          </TableHead>
          <TableBody>
            {clauses.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-gray-500">
                  No risks found
                </TableCell>
              </TableRow>
            ) : (
              clauses.map((clause: any, index: number) => (
                <TableRow key={index}>
                  <TableCell>
                    <div className="font-medium">{clause.title || 'Unnamed Clause'}</div>
                    <div className="text-xs text-gray-500">{clause.clause_id}</div>
                  </TableCell>
                  <TableCell>
                    <div className="max-w-md truncate">{clause.summary || 'No risk detected'}</div>
                  </TableCell>
                  <TableCell>
                    {clause.risk_level ? <RiskBadge level={clause.risk_level} /> : '-'}
                  </TableCell>
                  <TableCell>
                    <span
                      className={`text-xs px-2 py-1 rounded-full ${
                        clause.status === 'CONFIRMED'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {clause.status || 'PENDING'}
                    </span>
                  </TableCell>
                  <TableCell>
                    {clause.risk_id && (
                      <Link to={`/review/${taskId}`}>
                        <Button size="sm" variant="ghost">
                          Review
                        </Button>
                      </Link>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {isTaskComplete && (
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-medium text-blue-900 mb-2">📥 Reports</h3>
          <p className="text-sm text-blue-800 mb-3">
            Generate downloadable reports in HTML or JSON format. HTML reports include full
            formatting and can be printed or shared.
          </p>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => handleGenerateReport('html')}
              disabled={generatingReport}
            >
              Generate HTML
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => handleGenerateReport('json')}
              disabled={generatingReport}
            >
              Generate JSON
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
