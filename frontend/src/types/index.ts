export type ProductSku = {
  id?: number;
  product_id?: number;
  sku_no?: string;
  color_name?: string;
  color_code?: string;
  image_url?: string;
  color_remark?: string;
};

export type CopyOutput = {
  id?: number;
  product_id?: number;
  title?: string;
  main_image_tags: string[];
  color_copy?: string;
  source_basis?: string;
  llm_provider?: string;
  llm_model?: string;
  status?: string;
  hot_search_enabled?: boolean;
  selected_hot_terms?: string[];
  matched_hot_terms?: string[];
  missing_hot_terms?: string[];
  excluded_hot_terms?: Array<{ keyword: string; reason: string }>;
  hot_search_source_batch?: number | null;
  agent_mode?: string;
  agent_run_id?: number;
  agent_status?: string;
  agent_reflection?: string;
  agent_steps?: AgentRunStep[];
};

export type Product = {
  id?: number;
  style_no?: string;
  product_no?: string;
  category_3?: string;
  category_4?: string;
  age_range?: string;
  gender?: string;
  season?: string;
  scene?: string;
  fba?: string;
  remark?: string;
  status?: string;
  created_by?: string;
  updated_by?: string;
  skus: ProductSku[];
  copy_output?: CopyOutput | null;
};

export type CopyVersion = {
  id: number;
  version_no: number;
  version_type: string;
  title: string;
  main_image_tags: string[];
  color_copy: string;
  change_reason?: string;
  created_by?: string;
  created_at: string;
};

export type ValidationResult = {
  passed: boolean;
  errors: Array<{ field: string; message: string; value?: unknown }>;
  warnings: Array<{ field: string; message: string; value?: unknown }>;
};

export type Rule = {
  id?: number;
  rule_type: string;
  rule_name: string;
  content: string;
  enabled: boolean;
  updated_by?: string;
};

export type RuleSuggestion = {
  id: number;
  suggestion_type: string;
  content: string;
  source_basis?: string;
  sample_count: number;
  status: 'pending' | 'accepted' | 'rejected';
  created_by?: string;
};

export type LearningReport = {
  id: number;
  report_title: string;
  summary: string;
  sample_count: number;
  high_frequency_kept_terms_json: string[];
  high_frequency_removed_terms_json: string[];
  common_edit_patterns_json: string[];
  suggestions_json: string[];
  created_at: string;
};

export type LlmConfig = {
  id: number;
  provider: string;
  display_name?: string | null;
  base_url?: string | null;
  model: string;
  temperature: number;
  timeout_seconds: number;
  max_retries: number;
  enabled: boolean;
  updated_by?: string | null;
  api_key_set: boolean;
  created_at: string;
  updated_at: string;
};

export type LlmConfigPayload = {
  provider: string;
  display_name?: string | null;
  base_url?: string | null;
  api_key?: string | null;
  model: string;
  temperature: number;
  timeout_seconds: number;
  max_retries: number;
  enabled: boolean;
  updated_by?: string | null;
};

export type HotSearchConfig = {
  enabled_by_default: boolean;
  updated_by?: string | null;
};

export type AgentConfig = {
  enabled_by_default: boolean;
  default_agent_mode: string;
  allow_sdk_modes: boolean;
  available_modes: string[];
  updated_by?: string | null;
};

export type AgentRunStep = {
  id: number;
  run_id?: number;
  product_id?: number;
  skill_key: string;
  skill_name: string;
  status: string;
  input_json?: Record<string, unknown>;
  output_json?: Record<string, unknown>;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  error_message?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
};

export type AgentRun = {
  id: number;
  workspace_id?: number | null;
  product_id: number;
  mode: string;
  requested_mode?: string | null;
  status: string;
  summary?: string | null;
  error_message?: string | null;
  created_by?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  steps: AgentRunStep[];
};

export type WorkspaceRef = {
  id: number;
  name: string;
  slug: string;
  role: 'system_admin' | 'workspace_admin' | 'editor' | 'viewer';
};

export type AuthUser = {
  id: number;
  email: string;
  display_name: string;
  is_system_admin: boolean;
  workspaces: WorkspaceRef[];
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: AuthUser;
};

export type Workspace = {
  id: number;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
};

export type UserAccount = {
  id: number;
  email: string;
  display_name: string;
  is_active: boolean;
  is_system_admin: boolean;
  created_at: string;
  updated_at: string;
};

export type WorkspaceMember = {
  id: number;
  workspace_id: number;
  user_id: number;
  role: WorkspaceRef['role'] | 'workspace_admin' | 'editor' | 'viewer';
  email?: string | null;
  display_name?: string | null;
};

export type CopyBatch = {
  id: number;
  workspace_id: number;
  batch_no: string;
  status: string;
  filter_json: Record<string, unknown>;
  overwrite_existing: boolean;
  use_hot_search?: boolean | null;
  agent_mode?: string | null;
  total_count: number;
  pending_count: number;
  running_count: number;
  success_count: number;
  failed_count: number;
  skipped_count: number;
  canceled_count: number;
  created_by?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type CopyBatchItem = {
  id: number;
  batch_id: number;
  product_id: number;
  status: string;
  error_message?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type CopyBatchDetail = {
  batch: CopyBatch;
  items: CopyBatchItem[];
};
