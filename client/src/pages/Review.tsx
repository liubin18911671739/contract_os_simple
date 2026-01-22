import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTaskClauses, setTaskConclusion } from '../api/tasks';
import { Button } from '../components/ui/Button';
import { Tabs } from '../components/ui/Tabs';
import { RiskBadge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';

export default function Review() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [clauses, setClauses] = useState<any[]>([]);
  const [selectedClause, setSelectedClause] = useState<any>(null);
  const [notes, setNotes] = useState('');
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (!taskId) return;
    load();
  }, [taskId]);

  async function load() {
    try {
      const clausesData = (await getTaskClauses(taskId!)) as any[];
      setClauses(clausesData);
      if (clausesData.length > 0) {
        setSelectedClause(clausesData[0]);
      }
    } catch (error) {
      console.error('Failed to load clauses:', error);
    }
  }

  async function handleConclusion(conclusion: string) {
    try {
      await setTaskConclusion(taskId!, conclusion, notes);
      setSubmitted(true);
    } catch (error) {
      console.error('Failed to save conclusion:', error);
    }
  }

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'evidence', label: 'Evidence' },
    { id: 'actions', label: 'Actions' },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Review Risks</h2>
        <Button onClick={() => navigate(`/results/${taskId}`)}>Back to Results</Button>
      </div>

      {submitted && (
        <Alert type="success" className="mb-4">
          Conclusion saved successfully!
        </Alert>
      )}

      <div className="grid grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-medium mb-3">Clauses</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {clauses.map((clause: any, index: number) => (
              <div
                key={index}
                onClick={() => setSelectedClause(clause)}
                className={`p-3 rounded cursor-pointer ${
                  selectedClause?.clause_id === clause.clause_id
                    ? 'bg-blue-50 border-2 border-blue-500'
                    : 'bg-gray-50 hover:bg-gray-100'
                }`}
              >
                <div className="font-medium text-sm">{clause.title || 'Unnamed Clause'}</div>
                {clause.risk_level && <RiskBadge level={clause.risk_level} />}
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-2 bg-white rounded-lg shadow p-6">
          {selectedClause ? (
            <div>
              <div className="mb-4">
                <h3 className="text-lg font-medium">{selectedClause.title || 'Unnamed Clause'}</h3>
                {selectedClause.risk_level && <RiskBadge level={selectedClause.risk_level} />}
              </div>

              <Tabs tabs={tabs}>
                {(activeTab) => (
                  <div>
                    {activeTab === 'overview' && (
                      <div>
                        <div className="mb-4">
                          <h4 className="font-medium text-sm text-gray-500 mb-1">Risk Summary</h4>
                          <p className="text-gray-900">
                            {selectedClause.summary || 'No risk detected'}
                          </p>
                        </div>
                        <div>
                          <h4 className="font-medium text-sm text-gray-500 mb-1">Clause Text</h4>
                          <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                            {selectedClause.text?.substring(0, 500)}
                            {selectedClause.text?.length > 500 ? '...' : ''}
                          </p>
                        </div>
                      </div>
                    )}

                    {activeTab === 'evidence' && (
                      <div>
                        <h4 className="font-medium text-sm text-gray-500 mb-2">Evidence</h4>
                        <Alert type="info">
                          Evidence and KB citations would be displayed here in the full
                          implementation.
                        </Alert>
                      </div>
                    )}

                    {activeTab === 'actions' && (
                      <div>
                        <h4 className="font-medium text-sm text-gray-500 mb-2">Review Actions</h4>
                        <div className="space-y-3">
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => handleConclusion('CONFIRM')}
                          >
                            Confirm Risk
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleConclusion('DISMISS')}
                          >
                            Dismiss Risk
                          </Button>
                          <div className="mt-4">
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Notes
                            </label>
                            <textarea
                              value={notes}
                              onChange={(e) => setNotes(e.target.value)}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                              rows={3}
                              placeholder="Add review notes..."
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </Tabs>
            </div>
          ) : (
            <div className="text-center text-gray-500 py-12">Select a clause to review</div>
          )}
        </div>
      </div>
    </div>
  );
}
