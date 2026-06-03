from collections import Counter, defaultdict

from sqlalchemy.orm import Session

from app.models import CopyVersion, LearningReport, Rule, RuleSuggestion


def _latest_versions(db: Session, workspace_id: int | None = None) -> list[tuple[CopyVersion, CopyVersion]]:
    query = db.query(CopyVersion)
    if workspace_id is not None:
        query = query.filter(CopyVersion.workspace_id == workspace_id)
    versions = query.order_by(CopyVersion.product_id, CopyVersion.version_no).all()
    grouped: dict[int, dict[str, CopyVersion]] = defaultdict(dict)
    for version in versions:
        if version.version_type in ("model_generated", "manual_edit"):
            grouped[version.product_id][version.version_type] = version
    return [
        (items["model_generated"], items["manual_edit"])
        for items in grouped.values()
        if "model_generated" in items and "manual_edit" in items
    ]


def _tokenize(text: str | None) -> list[str]:
    text = text or ""
    return [text[i : i + 2] for i in range(max(len(text) - 1, 0)) if text[i : i + 2].strip()]


def analyze_learning(db: Session, workspace_id: int | None = None) -> LearningReport:
    pairs = _latest_versions(db, workspace_id)
    kept = Counter()
    removed = Counter()
    patterns = Counter()
    category_patterns = []
    for model_version, manual_version in pairs:
        model_terms = set(_tokenize(model_version.title) + model_version.main_image_tags)
        manual_terms = set(_tokenize(manual_version.title) + manual_version.main_image_tags)
        kept.update(manual_terms & model_terms)
        removed.update(model_terms - manual_terms)
        if model_version.title != manual_version.title:
            patterns["标题被人工压缩或重排核心卖点"] += 1
        if model_version.main_image_tags != manual_version.main_image_tags:
            patterns["主图卖点更偏向穿着利益点"] += 1
        if model_version.color_copy != manual_version.color_copy:
            patterns["颜色词更偏向场景化表达"] += 1
        category_patterns.append({"product_id": manual_version.product_id, "pattern": "人工编辑更偏好可感知利益点"})

    sample_count = len(pairs)
    top_kept = [term for term, _ in kept.most_common(8)]
    top_removed = [term for term, _ in removed.most_common(8)]
    common_patterns = [name for name, _ in patterns.most_common()] or ["暂无足够人工编辑样本"]
    summary = (
        f"基于{sample_count}组模型生成与人工编辑版本，人工编辑更偏好清晰利益点、短句标签和场景化颜色词。"
        if sample_count
        else "暂无可对比的模型生成与人工编辑版本，请先生成并人工保存文案。"
    )
    suggestions = [
        "标题规则应继续要求核心卖点前置，并减少无意义修饰词。",
        "主图卖点优先保留穿着体验和消费顾虑表达。",
    ]
    report = LearningReport(
        workspace_id=workspace_id,
        report_title="文案人工编辑学习报告",
        summary=summary,
        sample_count=sample_count,
        high_frequency_kept_terms_json=top_kept,
        high_frequency_removed_terms_json=top_removed,
        common_edit_patterns_json=common_patterns,
        category_patterns_json=category_patterns,
        suggestions_json=suggestions,
    )
    db.add(report)
    if sample_count:
        db.add(
            RuleSuggestion(
                workspace_id=workspace_id,
                suggestion_type="general",
                content="人工编辑更偏好可感知利益点，建议在生成规则中强化穿着体验、场景和顾虑解决表达。",
                source_basis="版本对比/人工修改",
                sample_count=sample_count,
                status="pending",
                created_by="system",
            )
        )
    db.commit()
    db.refresh(report)
    return report


def learning_summary(db: Session, workspace_id: int | None = None) -> dict:
    return {
        "reports": db.query(LearningReport).filter(LearningReport.workspace_id == workspace_id).count(),
        "pending_suggestions": db.query(RuleSuggestion).filter(RuleSuggestion.workspace_id == workspace_id, RuleSuggestion.status == "pending").count(),
        "manual_versions": db.query(CopyVersion).filter(CopyVersion.workspace_id == workspace_id, CopyVersion.version_type == "manual_edit").count(),
        "model_versions": db.query(CopyVersion).filter(CopyVersion.workspace_id == workspace_id, CopyVersion.version_type == "model_generated").count(),
    }


def accept_suggestion(db: Session, suggestion_id: int, reviewer: str, workspace_id: int | None = None) -> RuleSuggestion:
    suggestion = db.get(RuleSuggestion, suggestion_id)
    if not suggestion or suggestion.workspace_id != workspace_id:
        raise ValueError("规则建议不存在")
    suggestion.status = "accepted"
    suggestion.reviewed_by = reviewer
    from app.models import now

    suggestion.reviewed_at = now()
    db.add(
        Rule(
            workspace_id=workspace_id,
            rule_type=suggestion.suggestion_type,
            rule_name=f"学习建议-{suggestion.id}",
            content=f"{suggestion.content}\n\n依据：{suggestion.source_basis}",
            enabled=True,
            updated_by=reviewer,
        )
    )
    db.commit()
    db.refresh(suggestion)
    return suggestion


def reject_suggestion(db: Session, suggestion_id: int, reviewer: str, workspace_id: int | None = None) -> RuleSuggestion:
    suggestion = db.get(RuleSuggestion, suggestion_id)
    if not suggestion or suggestion.workspace_id != workspace_id:
        raise ValueError("规则建议不存在")
    suggestion.status = "rejected"
    suggestion.reviewed_by = reviewer
    from app.models import now

    suggestion.reviewed_at = now()
    db.commit()
    db.refresh(suggestion)
    return suggestion
