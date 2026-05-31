from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import CopyVersion, Product, RuleSuggestion
from app.services.learning_service import analyze_learning


def test_learning_analysis_creates_report_and_pending_suggestion():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    product = Product(style_no="A100", category_3="外套", category_4="防晒衣")
    db.add(product)
    db.commit()
    db.add_all(
        [
            CopyVersion(
                product_id=product.id,
                version_no=1,
                version_type="model_generated",
                title="清凉防晒舒适透气中大童女童防晒衣夏季出游轻薄外套",
                main_image_tags=["清凉防晒", "透气不闷", "出游好穿"],
                color_copy="清爽显白",
                created_by="model",
            ),
            CopyVersion(
                product_id=product.id,
                version_no=2,
                version_type="manual_edit",
                title="清凉防晒中大童女童防晒衣夏季出游轻薄舒适外套",
                main_image_tags=["清凉防晒", "轻薄好穿", "出游百搭"],
                color_copy="夏日百搭",
                created_by="operator",
            ),
        ]
    )
    db.commit()

    report = analyze_learning(db)

    assert report.sample_count == 1
    assert "人工编辑更偏好" in report.summary
    suggestion = db.query(RuleSuggestion).one()
    assert suggestion.status == "pending"
    assert suggestion.sample_count == 1
