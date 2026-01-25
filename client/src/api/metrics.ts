/**
 * Metrics API
 * API calls for evaluation dashboard metrics
 */

import { get } from './http';

export interface MetricsOverview {
  period: { start: string; end: string };
  total_tasks: number;
  completion_rate: number;
  avg_duration_seconds: number;
  risk_distribution: { high: number; medium: number; low: number; info: number };
  daily_breakdown: Array<{ date: string; tasks_created: number; tasks_completed: number }>;
}

export interface F1Score {
  f1_score: number;
  precision: number;
  recall: number;
}

export interface HallucinationRate {
  rate: number;
  trend: number;
}

export interface RiskLevelStats {
  total: number;
  confirmed: number;
  dismissed: number;
  pending: number;
  confirmation_rate: number;
  accuracy_rate: number;
}

export interface BaselineComparison {
  current_f1: number;
  baseline_f1: number;
  f1_change: number;
  current_precision: number;
  baseline_precision: number;
  precision_change: number;
  current_recall: number;
  baseline_recall: number;
  recall_change: number;
  current_hallucination: number;
  baseline_hallucination: number;
  hallucination_change: number;
  current_period: { start: string; end: string };
  baseline_period: { start: string; end: string };
}

export interface RiskAssessment {
  by_level: Record<string, RiskLevelStats>;
  by_type: Record<string, number>;
  overall_confirmation_rate: number;
  overall_accuracy: number;
  period: { start: string; end: string };
}

/**
 * Get metrics overview for a date range
 */
export async function getMetricsOverview(from: string, to: string): Promise<MetricsOverview> {
  return get<MetricsOverview>(`/metrics/overview?from=${from}&to=${to}`);
}

/**
 * Get F1 score metrics
 */
export async function getF1Score(from?: string, to?: string): Promise<F1Score> {
  let url = '/metrics/f1-score';
  const params = new URLSearchParams();
  if (from) params.append('from', from);
  if (to) params.append('to', to);
  if (params.toString()) url += '?' + params.toString();
  return get<F1Score>(url);
}

/**
 * Get hallucination rate metrics
 */
export async function getHallucinationRate(from?: string, to?: string): Promise<HallucinationRate> {
  let url = '/metrics/hallucination-rate';
  const params = new URLSearchParams();
  if (from) params.append('from', from);
  if (to) params.append('to', to);
  if (params.toString()) url += '?' + params.toString();
  return get<HallucinationRate>(url);
}

/**
 * Get baseline comparison - compare current period with previous period
 */
export async function getBaselineComparison(from: string, to: string): Promise<BaselineComparison> {
  return get<BaselineComparison>(`/metrics/baseline-comparison?from=${from}&to=${to}`);
}

/**
 * Get detailed risk assessment
 */
export async function getRiskAssessment(from: string, to: string): Promise<RiskAssessment> {
  return get<RiskAssessment>(`/metrics/risk-assessment?from=${from}&to=${to}`);
}
