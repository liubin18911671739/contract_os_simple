/**
 * Task API
 */
import { get, post } from './http';

export interface PrecheckTask {
  id: string;
  contract_version_id: string;
  status: string;
  progress: number;
  current_stage: string;
  cancel_requested: boolean;
  kb_mode: 'STRICT' | 'RELAXED';
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface TaskEvent {
  id: string;
  ts: string;
  stage: string;
  level: 'info' | 'warning' | 'error';
  message: string;
  meta?: any;
}

export interface CreateTaskParams {
  contract_version_id: string;
  kb_collection_ids: string[];
  kb_mode: 'STRICT' | 'RELAXED';
  template_id?: string;
}

export async function createTask(params: CreateTaskParams): Promise<{ id: string }> {
  return post('/precheck-tasks', params);
}

export async function getTask(taskId: string): Promise<PrecheckTask> {
  return get(`/precheck-tasks/${taskId}`);
}

export async function getTaskEvents(taskId: string): Promise<TaskEvent[]> {
  return get(`/precheck-tasks/${taskId}/events`);
}

export async function cancelTask(taskId: string): Promise<{ success: boolean }> {
  return post(`/precheck-tasks/${taskId}/cancel`);
}

export async function getTaskSummary(taskId: string) {
  return get(`/precheck-tasks/${taskId}/summary`);
}

export async function getTaskClauses(taskId: string, params?: { risk_level?: string; q?: string }) {
  const query = new URLSearchParams(params as any).toString();
  return get(`/precheck-tasks/${taskId}/clauses${query ? '?' + query : ''}`);
}

export async function setTaskConclusion(taskId: string, conclusion: string, notes?: string) {
  return post(`/precheck-tasks/${taskId}/conclusion`, { conclusion, notes });
}

export async function generateReport(taskId: string, format: 'html' | 'json' = 'html') {
  return post(`/precheck-tasks/${taskId}/report`, { format });
}

export async function getReportDownloadUrl(reportId: string): Promise<string> {
  // This returns the download URL which can be opened in a new tab
  return `/api/reports/${reportId}/download`;
}

export async function getTaskReports(taskId: string) {
  return get(`/precheck-tasks/${taskId}/reports`);
}
