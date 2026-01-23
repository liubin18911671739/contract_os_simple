import { vi } from 'vitest'

// Mock fetch API
export const mockFetch = vi.fn()

// Helper to setup successful fetch response
export function setupMockSuccessResponse(data: any) {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => data,
    status: 200,
  } as Response)
}

// Helper to setup failed fetch response
export function setupMockErrorResponse(error: string, status = 500) {
  mockFetch.mockResolvedValueOnce({
    ok: false,
    json: async () => ({ error }),
    status,
  } as Response)
}

// Reset all mocks
export function resetAllMocks() {
  mockFetch.mockReset()
  vi.clearAllMocks()
}

// Mock localStorage
export const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  get length() {
    return 0
  },
  key: vi.fn(),
}

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
})
