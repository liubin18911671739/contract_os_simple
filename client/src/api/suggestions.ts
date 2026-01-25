/**
 * Suggestions API
 * API calls for suggestion and risk level management
 */

import { get, post, put } from './http';

export interface Suggestion {
  id: string;
  risk_id: string;
  suggestion_text: string;
  created_by: string | null;
  created_at: string;
  revision_count: number;
}

export interface SuggestionRevision {
  id: string;
  suggestion_id: string;
  revision_no: number;
  suggestion_text: string;
  created_by: string | null;
  created_at: string;
}

export interface RuleHitInChain {
  id: string;
  rule_id: string;
  rule_name: string;
  matched_text: string;
  meta: Record<string, unknown>;
}

export interface KBCitationInChain {
  id: string;
  chunk_id: string | null;
  score: number;
  quote_text: string;
  doc_version: number;
  chunk: {
    id: string;
    chunk_no: number;
    text: string;
  } | null;
  document: {
    id: string;
    title: string;
    doc_type: string;
  } | null;
}

export interface EvidenceInChain {
  id: string;
  source_type: string;
  quote_text: string;
  start_offset: number | null;
  end_offset: number | null;
  page_ref: string | null;
  chunk_id: string | null;
}

export interface ClauseInChain {
  id: string;
  clause_id: string;
  title: string | null;
  text: string;
  page_ref: string | null;
  order_no: number;
}

export interface EvidenceChain {
  risk_id: string;
  task_id: string;
  risk_summary: string;
  risk_level: string;
  original_risk_level: string | null;
  risk_type: string;
  confidence: number;
  status: string;
  clause: ClauseInChain | null;
  rule_hits: RuleHitInChain[];
  kb_citations: KBCitationInChain[];
  evidences: EvidenceInChain[];
  suggestions: Suggestion[];
  adjusted_at: string | null;
  adjusted_by: string | null;
  adjustment_reason: string | null;
}

export interface RiskAdjustment {
  risk_level: string;
  reason?: string;
}

/**
 * Get suggestions for a risk
 */
export async function getSuggestions(riskId: string): Promise<Suggestion[]> {
  return get<Suggestion[]>(`/api/risks/${riskId}/suggestions`);
}

/**
 * Create a new suggestion
 */
export async function createSuggestion(
  riskId: string,
  suggestionText: string
): Promise<Suggestion> {
  return post<Suggestion>(`/api/risks/${riskId}/suggestions`, {
    suggestion_text: suggestionText,
  });
}

/**
 * Update a suggestion (creates a new revision)
 */
export async function updateSuggestion(
  suggestionId: string,
  newText: string
): Promise<SuggestionRevision> {
  return put<SuggestionRevision>(`/api/suggestions/${suggestionId}`, {
    suggestion_text: newText,
  });
}

/**
 * Get suggestion revision history
 */
export async function getSuggestionRevisions(
  suggestionId: string
): Promise<SuggestionRevision[]> {
  return get<SuggestionRevision[]>(
    `/api/suggestions/${suggestionId}/revisions`
  );
}

/**
 * Adjust risk level
 */
export async function adjustRiskLevel(
  riskId: string,
  adjustment: RiskAdjustment
): Promise<{
  id: string;
  risk_level: string;
  original_risk_level: string | null;
  adjusted_at: string | null;
  adjusted_by: string | null;
  adjustment_reason: string | null;
}> {
  return put(`/api/risks/${riskId}/level`, adjustment);
}

/**
 * Get complete evidence chain for a risk
 */
export async function getEvidenceChain(riskId: string): Promise<EvidenceChain> {
  return get<EvidenceChain>(`/api/risks/${riskId}/evidence-chain`);
}
