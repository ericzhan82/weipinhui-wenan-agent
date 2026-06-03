import type {
  CopyOutput,
  CopyVersion,
  HotSearchConfig,
  LearningReport,
  LlmConfig,
  LlmConfigPayload,
  Product,
  ProductSku,
  Rule,
  RuleSuggestion,
  ValidationResult,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

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

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: options.body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
      ...options,
    });
  } catch (error) {
    throw new Error(formatNetworkError(path, error));
  }
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(formatApiError(detail, response.status));
  }
  return response.json() as Promise<T>;
}

export const api = {
  products: (keyword = '') => request<Product[]>(`/products${keyword ? `?keyword=${encodeURIComponent(keyword)}` : ''}`),
  product: (id: number) => request<Product>(`/products/${id}`),
  createProduct: (payload: Product) => request<Product>('/products', { method: 'POST', body: JSON.stringify(payload) }),
  updateProduct: (id: number, payload: Partial<Product>) =>
    request<Product>(`/products/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteProduct: (id: number) => request<{ deleted: boolean }>(`/products/${id}`, { method: 'DELETE' }),
  createSku: (productId: number, payload: ProductSku) =>
    request<ProductSku>(`/products/${productId}/skus`, { method: 'POST', body: JSON.stringify(payload) }),
  updateSku: (id: number, payload: ProductSku) => request<ProductSku>(`/skus/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteSku: (id: number) => request<{ deleted: boolean }>(`/skus/${id}`, { method: 'DELETE' }),
  generateCopy: (productId: number, use_hot_search?: boolean) =>
    request<CopyOutput & { warnings: unknown[] }>(`/products/${productId}/generate-copy`, {
      method: 'POST',
      ...(use_hot_search === undefined ? {} : { body: JSON.stringify({ use_hot_search }) }),
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
};
