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
