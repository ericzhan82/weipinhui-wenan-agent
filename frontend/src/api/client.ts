import type {
  AgentConfig,
  AgentRun,
  AuthUser,
  CopyBatch,
  CopyBatchDetail,
  CopyOutput,
  CopyVersion,
  HotSearchConfig,
  LearningReport,
  LoginResponse,
  LlmConfig,
  LlmConfigPayload,
  Product,
  ProductSku,
  Rule,
  RuleSuggestion,
  UserAccount,
  ValidationResult,
  Workspace,
  WorkspaceMember,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';
const TOKEN_KEY = 'vipshop_copy_access_token';
const WORKSPACE_KEY = 'vipshop_copy_workspace_id';
const REQUEST_TIMEOUT_MS = 15000;

export type ProductFilters = {
  keyword?: string;
  status?: string;
  gender?: string;
  season?: string;
  context_status?: string;
  copy_state?: string;
};

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY) || '';
}

export function setAuthToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearAuthToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(WORKSPACE_KEY);
}

export function getWorkspaceId() {
  const value = localStorage.getItem(WORKSPACE_KEY);
  return value ? Number(value) : null;
}

export function setWorkspaceId(workspaceId: number | null) {
  if (workspaceId) localStorage.setItem(WORKSPACE_KEY, String(workspaceId));
  else localStorage.removeItem(WORKSPACE_KEY);
}

function formatUnknown(value: unknown): string {
  if (value == null) return '';
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) {
    return value.map(formatUnknown).filter(Boolean).join('；');
  }
  if (typeof value === 'object') {
    const record = value as Record<string, unknown>;
    const message = formatUnknown(record.message || record.msg || record.error);
    const validation = record.validation as Record<string, unknown> | undefined;
    const validationErrors = validation ? formatUnknown(validation.errors) : '';
    const validationWarnings = validation ? formatUnknown(validation.warnings) : '';
    return [message, validationErrors && `校验错误：${validationErrors}`, validationWarnings && `校验提醒：${validationWarnings}`]
      .filter(Boolean)
      .join('；') || JSON.stringify(value);
  }
  return String(value);
}

function formatApiError(detail: string, status: number): string {
  if (!detail) return `HTTP ${status}`;
  try {
    const parsed = JSON.parse(detail) as { detail?: unknown };
    return formatUnknown(parsed.detail ?? parsed) || `HTTP ${status}`;
  } catch {
    return detail;
  }
}

function formatNetworkError(path: string, error: unknown): string {
  const detail = error instanceof Error ? error.message : String(error);
  const target = `${API_BASE}${path}`;
  return `无法连接后端接口：${target}。请确认当前访问域名下的 /api 可达；云端部署请检查网关/Nginx 是否转发 /api、后端容器是否健康，以及跨域配置是否包含当前前端域名。原始错误：${detail}`;
}

function queryString(params: Record<string, string | undefined | null>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) search.set(key, value);
  });
  const text = search.toString();
  return text ? `?${text}` : '';
}

async function request<T>(path: string, options: RequestInit = {}, retryCount = 0): Promise<T> {
  let response: Response;
  const headers: Record<string, string> = {};
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  const token = getAuthToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const workspaceId = getWorkspaceId();
  if (workspaceId) headers['X-Workspace-Id'] = String(workspaceId);
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: { ...headers, ...(options.headers as Record<string, string> | undefined) },
      signal: options.signal || controller.signal,
    });
  } catch (error) {
    if ((options.method || 'GET').toUpperCase() === 'GET' && retryCount < 1) {
      window.clearTimeout(timeout);
      return request<T>(path, options, retryCount + 1);
    }
    throw new Error(formatNetworkError(path, error));
  } finally {
    window.clearTimeout(timeout);
  }
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(formatApiError(detail, response.status));
  }
  return response.json() as Promise<T>;
}

export const api = {
  login: (payload: { email: string; password: string }) =>
    request<LoginResponse>('/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  me: () => request<AuthUser>('/auth/me'),
  logout: () => request<{ ok: boolean }>('/auth/logout', { method: 'POST' }),
  workspaces: () => request<Workspace[]>('/workspaces'),
  createWorkspace: (payload: { name: string; slug?: string }) =>
    request<Workspace>('/workspaces', { method: 'POST', body: JSON.stringify(payload) }),
  users: () => request<UserAccount[]>('/users'),
  createUser: (payload: { email: string; display_name: string; password: string; is_system_admin: boolean; workspace_id?: number | null; role?: string }) =>
    request<UserAccount>('/users', { method: 'POST', body: JSON.stringify(payload) }),
  members: (workspaceId: number) => request<WorkspaceMember[]>(`/workspaces/${workspaceId}/members`),
  addMember: (workspaceId: number, payload: { user_id: number; role: string }) =>
    request<WorkspaceMember>(`/workspaces/${workspaceId}/members`, { method: 'POST', body: JSON.stringify(payload) }),
  updateMember: (workspaceId: number, userId: number, payload: { role: string }) =>
    request<WorkspaceMember>(`/workspaces/${workspaceId}/members/${userId}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteMember: (workspaceId: number, userId: number) =>
    request<{ deleted: boolean }>(`/workspaces/${workspaceId}/members/${userId}`, { method: 'DELETE' }),
  products: (filters: ProductFilters | string = '') => {
    const params = typeof filters === 'string' ? { keyword: filters } : filters;
    return request<Product[]>(`/products${queryString(params)}`);
  },
  product: (id: number) => request<Product>(`/products/${id}`),
  createProduct: (payload: Product) => request<Product>('/products', { method: 'POST', body: JSON.stringify(payload) }),
  updateProduct: (id: number, payload: Partial<Product>) =>
    request<Product>(`/products/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteProduct: (id: number) => request<{ deleted: boolean }>(`/products/${id}`, { method: 'DELETE' }),
  createSku: (productId: number, payload: ProductSku) =>
    request<ProductSku>(`/products/${productId}/skus`, { method: 'POST', body: JSON.stringify(payload) }),
  updateSku: (id: number, payload: ProductSku) => request<ProductSku>(`/skus/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteSku: (id: number) => request<{ deleted: boolean }>(`/skus/${id}`, { method: 'DELETE' }),
  generateCopy: (productId: number, use_hot_search?: boolean, agent_mode?: string) =>
    request<CopyOutput & { warnings: unknown[] }>(`/products/${productId}/generate-copy`, {
      method: 'POST',
      ...(use_hot_search === undefined && !agent_mode ? {} : { body: JSON.stringify({ use_hot_search, agent_mode }) }),
    }),
  generateCopyJob: (productId: number, use_hot_search?: boolean, agent_mode?: string) =>
    request<CopyBatch>(`/products/${productId}/generate-copy-job`, {
      method: 'POST',
      ...(use_hot_search === undefined && !agent_mode ? {} : { body: JSON.stringify({ use_hot_search, agent_mode }) }),
    }),
  rewriteCopy: (productId: number, rewrite_instruction: string, operator_name: string) =>
    request<CopyOutput>(`/products/${productId}/rewrite-copy`, {
      method: 'POST',
      body: JSON.stringify({ rewrite_instruction, operator_name }),
    }),
  saveCopy: (productId: number, payload: { title: string; main_image_tags: string[]; color_copy: string; operator_name: string; change_reason: string }) =>
    request<CopyOutput>(`/products/${productId}/copy`, { method: 'PUT', body: JSON.stringify(payload) }),
  validateCopy: (productId: number, payload: Partial<CopyOutput> & { operator_name: string }) =>
    request<ValidationResult>(`/products/${productId}/validate-copy`, { method: 'POST', body: JSON.stringify(payload) }),
  versions: (productId: number) => request<CopyVersion[]>(`/products/${productId}/copy-versions`),
  restoreVersion: (productId: number, versionId: number) =>
    request<CopyOutput>(`/products/${productId}/copy-versions/${versionId}/restore`, { method: 'POST' }),
  saveHistory: (productId: number, reason: string, operator_name: string) =>
    request(`/products/${productId}/save-history-case`, { method: 'POST', body: JSON.stringify({ reason, operator_name }) }),
  historyCases: (keyword = '') => request<Array<Record<string, unknown>>>(`/history-cases${keyword ? `?keyword=${encodeURIComponent(keyword)}` : ''}`),
  rules: () => request<Rule[]>('/rules'),
  createRule: (payload: Rule) => request<Rule>('/rules', { method: 'POST', body: JSON.stringify(payload) }),
  updateRule: (id: number, payload: Partial<Rule>) => request<Rule>(`/rules/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  disableRule: (id: number) => request(`/rules/${id}`, { method: 'DELETE' }),
  learningSummary: () => request<Record<string, number>>('/learning/summary'),
  analyzeLearning: () => request<LearningReport>('/learning/analyze', { method: 'POST' }),
  reports: () => request<LearningReport[]>('/learning/reports'),
  suggestions: () => request<RuleSuggestion[]>('/learning/suggestions'),
  acceptSuggestion: (id: number, reviewer: string) =>
    request<RuleSuggestion>(`/learning/suggestions/${id}/accept`, { method: 'POST', body: JSON.stringify({ reviewer }) }),
  rejectSuggestion: (id: number, reviewer: string) =>
    request<RuleSuggestion>(`/learning/suggestions/${id}/reject`, { method: 'POST', body: JSON.stringify({ reviewer }) }),
  llmStatus: () => request<Record<string, unknown>>('/llm/status'),
  llmConfigs: () => request<LlmConfig[]>('/llm/configs'),
  createLlmConfig: (payload: LlmConfigPayload) =>
    request<LlmConfig>('/llm/configs', { method: 'POST', body: JSON.stringify(payload) }),
  updateLlmConfig: (id: number, payload: Partial<LlmConfigPayload>) =>
    request<LlmConfig>(`/llm/configs/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  activateLlmConfig: (id: number) => request<LlmConfig>(`/llm/configs/${id}/activate`, { method: 'POST' }),
  hotSearchConfig: () => request<HotSearchConfig>('/hot-search/config'),
  updateHotSearchConfig: (payload: HotSearchConfig & { updated_by?: string }) =>
    request<HotSearchConfig>('/hot-search/config', { method: 'PUT', body: JSON.stringify(payload) }),
  agentConfig: () => request<AgentConfig>('/agent/config'),
  updateAgentConfig: (payload: AgentConfig & { updated_by?: string }) =>
    request<AgentConfig>('/agent/config', { method: 'PUT', body: JSON.stringify(payload) }),
  latestAgentRun: (productId: number) => request<AgentRun | null>(`/products/${productId}/agent-runs/latest`),
  importHotSearch: (file: File) => {
    const data = new FormData();
    data.append('file', file);
    return request<Record<string, unknown>>('/hot-search/import', { method: 'POST', body: data });
  },
  importExcel: (file: File) => {
    const data = new FormData();
    data.append('file', file);
    return request<Record<string, unknown>>('/excel/import', { method: 'POST', body: data });
  },
  exportExcel: (keyword = '') => request<{ export_id: string; download_url: string }>(`/excel/export${keyword ? `?keyword=${encodeURIComponent(keyword)}` : ''}`),
  createCopyBatch: (payload: ProductFilters & { overwrite_existing?: boolean; use_hot_search?: boolean | null; agent_mode?: string | null }) =>
    request<CopyBatch>('/copy-batches', { method: 'POST', body: JSON.stringify(payload) }),
  copyBatches: () => request<CopyBatch[]>('/copy-batches'),
  copyBatch: (batchNo: string) => request<CopyBatchDetail>(`/copy-batches/${encodeURIComponent(batchNo)}`),
  cancelCopyBatch: (batchNo: string) => request<CopyBatch>(`/copy-batches/${encodeURIComponent(batchNo)}/cancel`, { method: 'POST' }),
  retryCopyBatch: (batchNo: string) => request<CopyBatch>(`/copy-batches/${encodeURIComponent(batchNo)}/retry-failed`, { method: 'POST' }),
  exportCopyBatch: (batchNo: string) => request<{ export_id: string; filename: string; download_url: string }>(`/copy-batches/${encodeURIComponent(batchNo)}/export`),
};
