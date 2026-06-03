from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .db import Base


def now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    style_no: Mapped[str | None] = mapped_column(String(120), index=True)
    product_no: Mapped[str | None] = mapped_column(String(120), index=True)
    category_3: Mapped[str | None] = mapped_column(String(120), index=True)
    category_4: Mapped[str | None] = mapped_column(String(120), index=True)
    age_range: Mapped[str | None] = mapped_column(String(80))
    gender: Mapped[str | None] = mapped_column(String(40), index=True)
    season: Mapped[str | None] = mapped_column(String(80), index=True)
    scene: Mapped[str | None] = mapped_column(String(160), index=True)
    fba: Mapped[str | None] = mapped_column(Text)
    remark: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    created_by: Mapped[str | None] = mapped_column(String(80))
    updated_by: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    skus: Mapped[list["ProductSku"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    copy_output: Mapped["CopyOutput | None"] = relationship(
        back_populates="product", cascade="all, delete-orphan", uselist=False
    )
    versions: Mapped[list["CopyVersion"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class ProductSku(Base):
    __tablename__ = "product_skus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    sku_no: Mapped[str | None] = mapped_column(String(120), index=True)
    color_name: Mapped[str | None] = mapped_column(String(120), index=True)
    color_code: Mapped[str | None] = mapped_column(String(80))
    image_url: Mapped[str | None] = mapped_column(Text)
    color_remark: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    product: Mapped[Product] = relationship(back_populates="skus")


class CopyOutput(Base):
    __tablename__ = "copy_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), unique=True, index=True)
    title: Mapped[str | None] = mapped_column(Text)
    main_image_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    color_copy: Mapped[str | None] = mapped_column(Text)
    source_basis: Mapped[str | None] = mapped_column(Text)
    llm_provider: Mapped[str | None] = mapped_column(String(80))
    llm_model: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="draft")
    created_by: Mapped[str | None] = mapped_column(String(80))
    updated_by: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    product: Mapped[Product] = relationship(back_populates="copy_output")
    versions: Mapped[list["CopyVersion"]] = relationship(back_populates="copy_output")


class CopyVersion(Base):
    __tablename__ = "copy_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    copy_output_id: Mapped[int | None] = mapped_column(ForeignKey("copy_outputs.id"), nullable=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    version_type: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str | None] = mapped_column(Text)
    main_image_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    color_copy: Mapped[str | None] = mapped_column(Text)
    change_reason: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    product: Mapped[Product] = relationship(back_populates="versions")
    copy_output: Mapped[CopyOutput | None] = relationship(back_populates="versions")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    copy_output_id: Mapped[int | None] = mapped_column(ForeignKey("copy_outputs.id"), nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    errors_json: Mapped[list[dict]] = mapped_column(JSON, default=list)
    warnings_json: Mapped[list[dict]] = mapped_column(JSON, default=list)
    checked_by: Mapped[str | None] = mapped_column(String(80))
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    rule_type: Mapped[str] = mapped_column(String(80), index=True)
    rule_name: Mapped[str] = mapped_column(String(160), index=True)
    content: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)
    updated_by: Mapped[str | None] = mapped_column(String(80))


class HistoryCase(Base):
    __tablename__ = "history_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    style_no: Mapped[str | None] = mapped_column(String(120), index=True)
    category_3: Mapped[str | None] = mapped_column(String(120), index=True)
    category_4: Mapped[str | None] = mapped_column(String(120), index=True)
    age_range: Mapped[str | None] = mapped_column(String(80))
    gender: Mapped[str | None] = mapped_column(String(40), index=True)
    season: Mapped[str | None] = mapped_column(String(80), index=True)
    scene: Mapped[str | None] = mapped_column(String(160), index=True)
    fba: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    main_image_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    color_copy: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class RuleSuggestion(Base):
    __tablename__ = "rule_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    suggestion_type: Mapped[str] = mapped_column(String(80), index=True)
    content: Mapped[str] = mapped_column(Text)
    source_basis: Mapped[str | None] = mapped_column(Text)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    created_by: Mapped[str | None] = mapped_column(String(80), default="system")
    reviewed_by: Mapped[str | None] = mapped_column(String(80))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class LearningReport(Base):
    __tablename__ = "learning_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    report_title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    high_frequency_kept_terms_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    high_frequency_removed_terms_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    common_edit_patterns_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    category_patterns_json: Mapped[list[dict]] = mapped_column(JSON, default=list)
    suggestions_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class LlmConfig(Base):
    __tablename__ = "llm_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(80), index=True)
    display_name: Mapped[str | None] = mapped_column(String(120))
    base_url: Mapped[str | None] = mapped_column(Text)
    api_key: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(160))
    temperature: Mapped[float] = mapped_column(Float, default=0.4)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=90)
    max_retries: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    updated_by: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class HotSearchConfig(Base):
    __tablename__ = "hot_search_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    enabled_by_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    updated_by: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class HotSearchBatch(Base):
    __tablename__ = "hot_search_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    filename: Mapped[str | None] = mapped_column(String(240))
    uploaded_by: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)

    terms: Mapped[list["HotSearchTerm"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class HotSearchTerm(Base):
    __tablename__ = "hot_search_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("hot_search_batches.id"), index=True)
    category: Mapped[str] = mapped_column(String(160), index=True)
    keyword: Mapped[str] = mapped_column(String(240), index=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    search_uv_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    search_uv_growth: Mapped[float | None] = mapped_column(Float, nullable=True)
    click_rate_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    opportunity_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    gmv_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    sales_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    batch: Mapped[HotSearchBatch] = relationship(back_populates="terms")


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    style_no: Mapped[str | None] = mapped_column(String(120), index=True)
    exposure_count: Mapped[int] = mapped_column(Integer, default=0)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    click_rate: Mapped[float] = mapped_column(Float, default=0)
    conversion_count: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0)
    order_count: Mapped[int] = mapped_column(Integer, default=0)
    gmv: Mapped[float] = mapped_column(Float, default=0)
    metric_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_system_admin: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class WorkspaceMembership(Base):
    __tablename__ = "workspace_memberships"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(40), default="editor", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class CopyBatch(Base):
    __tablename__ = "copy_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    batch_no: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="queued", index=True)
    filter_json: Mapped[dict] = mapped_column(JSON, default=dict)
    overwrite_existing: Mapped[bool] = mapped_column(Boolean, default=False)
    use_hot_search: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    pending_count: Mapped[int] = mapped_column(Integer, default=0)
    running_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    canceled_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str | None] = mapped_column(String(120))
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class CopyBatchItem(Base):
    __tablename__ = "copy_batch_items"
    __table_args__ = (UniqueConstraint("batch_id", "product_id", name="uq_copy_batch_product"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("copy_batches.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)
