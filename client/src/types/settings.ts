/**
 * Settings type definitions
 */

// User settings
export interface UserSettings {
  name: string;
  department: string;
  email?: string;
  avatar?: string;
}

// Application preferences
export interface AppPreferences {
  language: 'zh-CN' | 'en-US';
  theme: 'light' | 'dark';
  notifications: boolean;
}

// LLM configuration
export interface LLMConfig {
  provider: 'local' | 'zhipu';
  chatModel: string;
  embedModel: string;
  rerankModel: string;
  chatBaseUrl?: string;
  embedBaseUrl?: string;
  rerankBaseUrl?: string;
  apiKey?: string;
}

// Knowledge base configuration
export interface KBConfig {
  chunkSize: number;
  chunkOverlap: number;
  topK: number;
  topN: number;
}

// Complete settings
export interface Settings {
  user: UserSettings;
  preferences: AppPreferences;
  llm: LLMConfig;
  kb: KBConfig;
}

// Default settings
export const DEFAULT_SETTINGS: Settings = {
  user: {
    name: '张律师',
    department: '法务部',
    email: '',
    avatar: ''
  },
  preferences: {
    language: 'zh-CN',
    theme: 'light',
    notifications: true
  },
  llm: {
    provider: 'zhipu',
    chatModel: 'glm-4-flash',
    embedModel: 'embedding-3',
    rerankModel: 'rerank-2'
  },
  kb: {
    chunkSize: 1000,
    chunkOverlap: 200,
    topK: 20,
    topN: 6
  }
};

// Model options for different providers
export const MODEL_OPTIONS = {
  local: {
    chat: ['Qwen/Qwen2.5-7B-Instruct', 'Qwen/Qwen2.5-14B-Instruct'],
    embed: ['BAAI/bge-m3', 'BAAI/bge-large-zh-v1.5'],
    rerank: ['BAAI/bge-reranker-v2-m3']
  },
  zhipu: {
    chat: ['glm-4-flash', 'glm-4-plus', 'glm-4-0520'],
    embed: ['embedding-3', 'embedding-2'],
    rerank: ['rerank-2']
  }
} as const;

// Department options
export const DEPARTMENT_OPTIONS = [
  { value: '法务部', label: '法务部' },
  { value: '合规部', label: '合规部' },
  { value: '风控部', label: '风控部' },
  { value: '技术部', label: '技术部' }
];

// Language options
export const LANGUAGE_OPTIONS = [
  { value: 'zh-CN', label: '中文' },
  { value: 'en-US', label: 'English' }
];

// Theme options
export const THEME_OPTIONS = [
  { value: 'light', label: '浅色' },
  { value: 'dark', label: '深色' }
];

// Provider options
export const PROVIDER_OPTIONS = [
  { value: 'local', label: '本地 vLLM' },
  { value: 'zhipu', label: '智谱 Qingyan' }
];
