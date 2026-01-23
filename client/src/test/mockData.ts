// Mock task data
export const mockTasks = [
  {
    id: '1',
    contract_name: '供应商服务合同',
    status: 'COMPLETED',
    progress: 100,
    current_stage: 'DONE',
    error_message: null,
    cancel_requested: false,
    kb_mode: 'STRICT',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:10:00Z',
  },
  {
    id: '2',
    contract_name: '劳动合同',
    status: 'PROCESSING',
    progress: 75,
    current_stage: 'LLM_RISK',
    error_message: null,
    cancel_requested: false,
    kb_mode: 'RELAXED',
    created_at: '2024-01-01T01:00:00Z',
    updated_at: '2024-01-01T01:05:00Z',
  },
  {
    id: '3',
    contract_name: '采购协议',
    status: 'FAILED',
    progress: 50,
    current_stage: 'KB_RETRIEVAL',
    error_message: 'API rate limit exceeded',
    cancel_requested: false,
    kb_mode: 'STRICT',
    created_at: '2024-01-01T02:00:00Z',
    updated_at: '2024-01-01T02:05:00Z',
  },
]

// Mock contract data
export const mockContracts = [
  {
    id: '1',
    contract_name: '供应商服务合同',
    counterparty: '某某科技有限公司',
    contract_type: '采购合同',
    created_at: '2024-01-01T00:00:00Z',
    versions: [
      {
        id: '1',
        version_number: 1,
        file_name: 'contract_v1.pdf',
        upload_time: '2024-01-01T00:00:00Z',
        status: 'ACTIVE',
      },
    ],
  },
  {
    id: '2',
    contract_name: '劳动合同',
    counterparty: '张三',
    contract_type: '劳动合同',
    created_at: '2024-01-01T01:00:00Z',
    versions: [],
  },
]

// Mock KB collection data
export const mockKBCollections = [
  {
    id: '1',
    name: '合同法规知识库',
    scope: 'GLOBAL',
    version: 1,
    is_enabled: true,
    document_count: 15,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: '合同最佳实践',
    scope: 'GLOBAL',
    version: 1,
    is_enabled: true,
    document_count: 8,
    created_at: '2024-01-02T00:00:00Z',
  },
]

// Mock task summary data
export const mockTaskSummary = {
  clause_count: 25,
  high_risks: 3,
  medium_risks: 8,
  low_risks: 12,
  info_risks: 2,
}

// Mock clauses with risks
export const mockClauses = [
  {
    id: '1',
    clause_id: 'clause_001',
    title: '第一条 合同标的',
    text: '甲方向乙方采购...',
    order_no: 1,
    risk_id: '1',
    risk_level: 'HIGH',
    risk_summary: '存在不平等条款风险',
    risk_status: 'PENDING',
  },
  {
    id: '2',
    clause_id: 'clause_002',
    title: '第二条 付款方式',
    text: '付款方式为...',
    order_no: 2,
    risk_id: null,
    risk_level: null,
    risk_summary: null,
    risk_status: null,
  },
]

// Mock dashboard stats
export const mockDashboardStats = {
  total_tasks: 150,
  active_tasks: 5,
  completed_tasks: 140,
  failed_tasks: 5,
  total_contracts: 50,
  total_kb_collections: 3,
}

// Mock API response wrapper
export function mockApiResponse<T>(data: T, delay = 0) {
  return new Promise<{ data: T }>(resolve => {
    setTimeout(() => {
      resolve({ data })
    }, delay)
  })
}

// Mock API error
export function mockApiError(message: string, status = 500) {
  return Promise.reject({
    response: {
      status,
      data: { error: message },
    },
  })
}
