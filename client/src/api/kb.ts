/**
 * Knowledge Base API
 */
import { get, post, uploadFile } from './http';

export interface KBCollection {
  id: string;
  name: string;
  scope: 'GLOBAL' | 'TENANT' | 'PROJECT' | 'DEPT';
  version: number;
  is_enabled: boolean;
  created_at: string;
}

export interface KBDocument {
  id: string;
  collection_id: string;
  title: string;
  doc_type: string;
  created_at: string;
}

export interface KBSearchResult {
  chunk_id: string;
  text: string;
  score: number;
  doc_title: string;
  doc_version: number;
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

export async function searchKB(data: {
  query: string;
  collection_ids?: string[];
  top_k?: number;
  task_id?: string;
}): Promise<KBSearchResult[]> {
  return post('/kb/search', data);
}

export async function getKBChunk(chunkId: string) {
  return get(`/kb/chunks/${chunkId}`);
}
