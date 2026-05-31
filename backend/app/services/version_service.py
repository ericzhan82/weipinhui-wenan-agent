from sqlalchemy.orm import Session

from app.models import CopyOutput, CopyVersion


def next_version_no(db: Session, product_id: int) -> int:
    latest = (
        db.query(CopyVersion)
        .filter(CopyVersion.product_id == product_id)
        .order_by(CopyVersion.version_no.desc())
        .first()
    )
    return (latest.version_no if latest else 0) + 1


def create_copy_version(
    db: Session,
    product_id: int,
    copy_output: CopyOutput | None,
    version_type: str,
    title: str,
    main_image_tags: list[str],
    color_copy: str,
    created_by: str,
    change_reason: str | None = None,
) -> CopyVersion:
    version = CopyVersion(
        copy_output_id=copy_output.id if copy_output else None,
        product_id=product_id,
        version_no=next_version_no(db, product_id),
        version_type=version_type,
        title=title,
        main_image_tags=main_image_tags,
        color_copy=color_copy,
        change_reason=change_reason,
        created_by=created_by,
    )
    db.add(version)
    return version
