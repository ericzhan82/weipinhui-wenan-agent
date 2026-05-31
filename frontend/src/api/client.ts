import type {
  CopyOutput,
  CopyVersion,
  LearningReport,
  Product,
  ProductSku,
  Rule,
  RuleSuggestion,
  ValidationResult,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: options.body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    let parsedDetail = '';
    try {
      const parsed = JSON.parse(detail);
      parsedDetail = parsed.detail || '';
    } catch {
      parsedDetail = '';
    }
    throw new Error(parsedDetail || detail || `HTTP ${response.status}`);
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
  generateCopy: (productId: number) => request<CopyOutput & { warnings: unknown[] }>(`/products/${productId}/generate-copy`, { method: 'POST' }),
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
  importExcel: (file: File) => {
    const data = new FormData();
    data.append('file', file);
    return request<Record<string, unknown>>('/excel/import', { method: 'POST', body: data });
  },
  exportExcel: (keyword = '') => request<{ export_id: string; download_url: string }>(`/excel/export${keyword ? `?keyword=${encodeURIComponent(keyword)}` : ''}`),
};
