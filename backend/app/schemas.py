from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SkuBase(BaseModel):
    sku_no: str | None = None
    color_name: str | None = None
    color_code: str | None = None
    image_url: str | None = None
    color_remark: str | None = None


class SkuCreate(SkuBase):
    pass


class SkuUpdate(SkuBase):
    pass


class SkuRead(SkuBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    created_at: datetime
    updated_at: datetime


class ProductBase(BaseModel):
    style_no: str | None = None
    product_no: str | None = None
    category_3: str | None = None
    category_4: str | None = None
    age_range: str | None = None
    gender: str | None = None
    season: str | None = None
    scene: str | None = None
    fba: str | None = None
    remark: str | None = None
    status: str = "draft"
    created_by: str | None = None
    updated_by: str | None = None


class ProductCreate(ProductBase):
    skus: list[SkuCreate] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    style_no: str | None = None
    product_no: str | None = None
    category_3: str | None = None
    category_4: str | None = None
    age_range: str | None = None
    gender: str | None = None
    season: str | None = None
    scene: str | None = None
    fba: str | None = None
    remark: str | None = None
    status: str | None = None
    updated_by: str | None = None


class CopyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    title: str | None
    main_image_tags: list[str]
    color_copy: str | None
    source_basis: str | None
    llm_provider: str | None
    llm_model: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int | None = None
    skus: list[SkuRead] = Field(default_factory=list)
    copy_output: CopyRead | None = None
    created_at: datetime
    updated_at: datetime


class CopySaveRequest(BaseModel):
    title: str
    main_image_tags: list[str]
    color_copy: str
    operator_name: str = "operator"
    change_reason: str = "人工优化"


class RewriteCopyRequest(BaseModel):
    rewrite_instruction: str
    operator_name: str = "operator"


class ValidateCopyRequest(BaseModel):
    title: str | None = None
    main_image_tags: list[str] | None = None
    color_copy: str | None = None
    operator_name: str = "operator"


class CopyGenerateRequest(BaseModel):
    use_hot_search: bool | None = None
    agent_mode: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthUserRead(BaseModel):
    id: int
    email: str
    display_name: str
    is_system_admin: bool
    workspaces: list[dict[str, Any]] = Field(default_factory=list)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserRead


class WorkspaceCreate(BaseModel):
    name: str
    slug: str | None = None


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    email: str
    display_name: str
    password: str
    is_system_admin: bool = False
    workspace_id: int | None = None
    role: str = "editor"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    is_active: bool
    is_system_admin: bool
    created_at: datetime
    updated_at: datetime


class WorkspaceMemberCreate(BaseModel):
    user_id: int
    role: str = "editor"


class WorkspaceMemberUpdate(BaseModel):
    role: str


class WorkspaceMemberRead(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    role: str
    email: str | None = None
    display_name: str | None = None


class CopyBatchCreate(BaseModel):
    keyword: str | None = None
    status: str | None = None
    gender: str | None = None
    season: str | None = None
    context_status: str | None = None
    copy_state: str | None = None
    overwrite_existing: bool = False
    use_hot_search: bool | None = None
    agent_mode: str | None = None


class CopyBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    batch_no: str
    status: str
    filter_json: dict[str, Any]
    overwrite_existing: bool
    use_hot_search: bool | None
    agent_mode: str | None = None
    total_count: int
    pending_count: int
    running_count: int
    success_count: int
    failed_count: int
    skipped_count: int
    canceled_count: int
    created_by: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CopyBatchItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    product_id: int
    status: str
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CopyBatchDetail(BaseModel):
    batch: CopyBatchRead
    items: list[CopyBatchItemRead]


class HotSearchConfigUpdate(BaseModel):
    enabled_by_default: bool
    updated_by: str = "operator"


class AgentConfigUpdate(BaseModel):
    enabled_by_default: bool
    default_agent_mode: str = "legacy"
    allow_sdk_modes: bool = False
    updated_by: str = "operator"


class AgentConfigRead(BaseModel):
    enabled_by_default: bool
    default_agent_mode: str
    allow_sdk_modes: bool
    available_modes: list[str]
    updated_by: str | None = None


class AgentRunStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    product_id: int
    skill_key: str
    skill_name: str
    status: str
    input_json: dict[str, Any]
    output_json: dict[str, Any]
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class AgentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int | None
    product_id: int
    mode: str
    requested_mode: str | None
    status: str
    summary: str | None
    error_message: str | None
    created_by: str | None
    started_at: datetime
    finished_at: datetime | None
    steps: list[AgentRunStepRead] = Field(default_factory=list)


class HistoryCaseCreate(BaseModel):
    reason: str = "人工确认优秀案例"
    operator_name: str = "operator"


class RuleBase(BaseModel):
    rule_type: str
    rule_name: str
    content: str
    enabled: bool = True
    updated_by: str | None = None


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    rule_type: str | None = None
    rule_name: str | None = None
    content: str | None = None
    enabled: bool | None = None
    updated_by: str | None = None


class RuleRead(RuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class SuggestionReviewRequest(BaseModel):
    reviewer: str = "operator"


class ImportResult(BaseModel):
    success_count: int
    failed_rows: list[dict[str, Any]]
    skipped_count: int = 0
    updated_count: int = 0


class ExportResult(BaseModel):
    export_id: str
    filename: str
    download_url: str


class LlmConfigBase(BaseModel):
    provider: str
    display_name: str | None = None
    base_url: str | None = None
    model: str
    temperature: float = 0.4
    timeout_seconds: int = 90
    max_retries: int = 0
    enabled: bool = True
    updated_by: str | None = "operator"


class LlmConfigCreate(LlmConfigBase):
    api_key: str | None = None


class LlmConfigUpdate(BaseModel):
    provider: str | None = None
    display_name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    temperature: float | None = None
    timeout_seconds: int | None = None
    max_retries: int | None = None
    enabled: bool | None = None
    updated_by: str | None = None


class LlmConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    display_name: str | None
    base_url: str | None
    model: str
    temperature: float
    timeout_seconds: int
    max_retries: int
    enabled: bool
    updated_by: str | None
    api_key_set: bool
    created_at: datetime
    updated_at: datetime
