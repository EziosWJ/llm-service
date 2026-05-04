from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, Form, UploadFile

from src.bootstrap import get_container

router = APIRouter(prefix="/materials", tags=["materials"])


@router.post("/process")
async def process_material(
    file: UploadFile = File(...),
    material_id: str = Form(...),
    user_id: str = Form(...),
) -> dict[str, int]:
    suffix = Path(file.filename or "").suffix
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    try:
        container = get_container()
        return container.material_pipeline.process_file(
            file_path=tmp_path,
            material_id=material_id,
            user_id=user_id,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


@router.delete("/{material_id}/vectors")
def delete_vectors(material_id: str, user_id: str | None = None) -> dict[str, int]:
    container = get_container()
    deleted_count = container.qdrant_store.delete_by_material_id(material_id, user_id=user_id)
    return {"deleted_count": deleted_count}
