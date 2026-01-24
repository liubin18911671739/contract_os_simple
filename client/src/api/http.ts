/**
 * HTTP client for API calls
 * Includes request/response logging and performance monitoring
 */
import { log } from '../utils/logger';

const API_BASE = '/api';

interface RequestTiming {
  startTime: number;
  path: string;
  method: string;
}

// Track active requests for debugging
const activeRequests = new Map<string, RequestTiming>();

function startTiming(method: string, path: string): string {
  const requestId = `${method}:${path}:${Date.now()}`;
  const startTime = performance.now();
  activeRequests.set(requestId, { startTime, path, method });
  log.apiRequest(method, path);
  return requestId;
}

function endTiming(requestId: string, status: number): number {
  const timing = activeRequests.get(requestId);
  if (timing) {
    const duration = performance.now() - timing.startTime;
    activeRequests.delete(requestId);
    log.apiResponse(timing.method, timing.path, status, duration);
    return duration;
  }
  return 0;
}

function getErrorCode(status: number, responseText?: string): string {
  // Try to extract error detail from response
  if (responseText) {
    try {
      const errorData = JSON.parse(responseText);
      if (errorData.detail) return errorData.detail;
      if (errorData.message) return errorData.message;
      if (errorData.error) return errorData.error;
    } catch {
      // Not JSON, return as-is
    }
  }
  return `HTTP error! status: ${status}`;
}

export async function get<T>(path: string): Promise<T> {
  const requestId = startTiming('GET', path);
  let status = 0;

  try {
    const response = await fetch(`${API_BASE}${path}`);
    status = response.status;
    endTiming(requestId, status);

    if (!response.ok) {
      const responseText = await response.text();
      const errorDetail = getErrorCode(status, responseText);
      log.apiError('GET', path, new Error(errorDetail), endTiming(requestId, status));
      throw new Error(errorDetail);
    }
    return response.json();
  } catch (error: any) {
    if (status === 0) {
      log.apiError('GET', path, error);
    }
    throw error;
  }
}

export async function post<T>(path: string, data?: any): Promise<T> {
  const requestId = startTiming('POST', path);
  let status = 0;

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    status = response.status;
    endTiming(requestId, status);

    if (!response.ok) {
      const responseText = await response.text();
      const errorDetail = getErrorCode(status, responseText);
      log.apiError('POST', path, new Error(errorDetail), endTiming(requestId, status));
      throw new Error(errorDetail);
    }
    return response.json();
  } catch (error: any) {
    if (status === 0) {
      log.apiError('POST', path, error);
    }
    throw error;
  }
}

export async function del<T>(path: string): Promise<T> {
  const requestId = startTiming('DELETE', path);
  let status = 0;

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'DELETE',
    });
    status = response.status;
    endTiming(requestId, status);

    if (!response.ok) {
      const responseText = await response.text();
      const errorDetail = getErrorCode(status, responseText);
      log.apiError('DELETE', path, new Error(errorDetail), endTiming(requestId, status));
      throw new Error(errorDetail);
    }
    return response.json();
  } catch (error: any) {
    if (status === 0) {
      log.apiError('DELETE', path, error);
    }
    throw error;
  }
}

export async function uploadFile<T>(
  path: string,
  file: File,
  additionalData: Record<string, string> = {}
): Promise<T> {
  const requestId = startTiming('UPLOAD', path);
  let status = 0;

  try {
    const formData = new FormData();
    formData.append('file', file);
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, value);
    });

    log.debug('Uploading file', {
      path,
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      additionalData,
    });

    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      body: formData,
    });
    status = response.status;
    endTiming(requestId, status);

    if (!response.ok) {
      const responseText = await response.text();
      const errorDetail = getErrorCode(status, responseText);
      log.apiError('UPLOAD', path, new Error(errorDetail), endTiming(requestId, status));
      throw new Error(errorDetail);
    }

    log.info('File uploaded successfully', { path, fileName: file.name });
    return response.json();
  } catch (error: any) {
    if (status === 0) {
      log.apiError('UPLOAD', path, error);
    }
    throw error;
  }
}

// Get active requests for debugging
export function getActiveRequests(): RequestTiming[] {
  return Array.from(activeRequests.values());
}

// Clear hung requests (call from error boundary or cleanup)
export function clearHungRequests(olderThanMs: number = 30000) {
  const now = performance.now();
  const toDelete: string[] = [];

  activeRequests.forEach((timing, requestId) => {
    if (now - timing.startTime > olderThanMs) {
      log.warn('Hung request detected', {
        method: timing.method,
        path: timing.path,
        duration: `${now - timing.startTime}ms`,
      });
      toDelete.push(requestId);
    }
  });

  toDelete.forEach(id => activeRequests.delete(id));
}
