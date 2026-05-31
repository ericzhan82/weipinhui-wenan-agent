from pathlib import Path

from sqlalchemy.orm import Session

from .models import Rule

DEFAULT_RULES = [
    ("general", "总规则", "不编造商品资料中不存在的材质、功能或场景；优先突出FBA中的核心利益点。"),
    ("title", "标题规则", "标题必须29-30个字符；结构为核心卖点+适用岁段+品类+性别+季节+场景。"),
    ("main_image", "主图打标卖点规则", "主图卖点最多3个，每个4-10个字符，优先表达穿着利益点。"),
    ("color", "颜色词文案规则", "颜色词文案必须4-6个字符，可结合颜色、场景和穿着体验。"),
    ("forbidden", "禁用词与风险词", "最强\n最佳\n第一\n顶级\n全网\n永久\n100%\n必买"),
]


def seed_default_rules(db: Session) -> None:
    if db.query(Rule).count() > 0:
        return
    rules_dir = Path(__file__).parent / "rules"
    file_rules = []
    if rules_dir.exists():
        for path in sorted(rules_dir.glob("*.md")):
            file_rules.append(("general", path.stem, path.read_text(encoding="utf-8")))
    for rule_type, rule_name, content in file_rules or DEFAULT_RULES:
        db.add(Rule(rule_type=rule_type, rule_name=rule_name, content=content, enabled=True, updated_by="system"))
    db.commit()
