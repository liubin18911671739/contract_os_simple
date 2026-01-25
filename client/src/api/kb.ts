/**
 * Knowledge Base API
 */
import { get, post, del, uploadFile } from './http';

export interface KBCollection {
  id: string;
  name: string;
  scope: 'GLOBAL' | 'TENANT' | 'PROJECT' | 'DEPT';
  version: number;
  is_enabled: boolean;
  document_count?: number;
  chunk_count?: number;
  indexed_count?: number;
  created_at: string;
}

export interface KBDocument {
  id: string;
  collection_id: string;
  title: string;
  doc_type: string;
  chunk_count: number;
  indexed_count: number;
  status: 'pending' | 'chunking' | 'indexing' | 'ready' | 'failed';
  created_at: string;
}

export interface KBSearchResult {
  chunk_id: string;
  text: string;
  score: number;
  doc_title: string;
  doc_version: number;
  doc_id?: string;
  collection_id?: string;
}

export interface KBChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  text: string;
  is_indexed: boolean;
  created_at: string;
}

export interface KBCollectionStats {
  id: string;
  name: string;
  document_count: number;
  chunk_count: number;
  indexed_count: number;
  avg_chunk_size: number;
  total_storage_mb: number;
}

export interface KBSearchParams {
  query: string;
  collection_ids?: string[];
  top_k?: number;
}

export async function createKBCollection(data: {
  name: string;
  scope: 'GLOBAL' | 'TENANT' | 'PROJECT' | 'DEPT';
}): Promise<{ id: string }> {
  return post('/kb/collections', data);
}

export async function getKBCollections(): Promise<KBCollection[]> {
  return get('/kb/collections');
}

export async function deleteKBCollection(collectionId: string): Promise<void> {
  return del(`/kb/collections/${collectionId}`);
}

export async function getKBCollectionStats(collectionId: string): Promise<KBCollectionStats> {
  return get(`/kb/collections/${collectionId}/stats`);
}

export async function uploadKBDocument(
  collectionId: string,
  file: File,
  title?: string
): Promise<{ id: string }> {
  return uploadFile('/kb/documents', file, {
    collection_id: collectionId,
    title: title || file.name,
    doc_type: 'txt',
  });
}

export async function getKBDocuments(collectionId?: string): Promise<KBDocument[]> {
  const query = collectionId ? `?collection_id=${collectionId}` : '';
  return get(`/kb/documents${query}`);
}

export async function deleteKBDocument(docId: string): Promise<void> {
  return del(`/kb/documents/${docId}`);
}

export async function getKBDocumentChunks(docId: string): Promise<KBChunk[]> {
  return get(`/kb/documents/${docId}/chunks`);
}

export async function getKBChunk(chunkId: string): Promise<KBChunk> {
  return get(`/kb/chunks/${chunkId}`);
}

export async function searchKB(params: KBSearchParams): Promise<KBSearchResult[]> {
  return post('/kb/search', params);
}
