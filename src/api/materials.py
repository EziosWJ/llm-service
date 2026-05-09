from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, Form, Query, UploadFile

from src.bootstrap import get_container
from src.models.errors import ValidationError
from src.models.responses import DeleteVectorsResponse, MaterialProcessResponse

router = APIRouter(prefix="/materials", tags=["materials"])
SUPPORTED_MATERIAL_SUFFIXES = {".txt", ".docx", ".pdf", ".md"}


@router.post("/process", response_model=MaterialProcessResponse)
async def process_material(
    file: UploadFile = File(...),
    material_id: str = Form(...),
    user_id: str = Form(...),
) -> MaterialProcessResponse:
    suffix = Path(file.filename or "").suffix
    if suffix.lower() not in SUPPORTED_MATERIAL_SUFFIXES:
        raise ValidationError("unsupported material file type")

    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    try:
        container = get_container()
        result = container.material_pipeline.process_file(
            file_path=tmp_path,
            material_id=material_id,
            user_id=user_id,
        )
        return MaterialProcessResponse(**result)
    finally:
        tmp_path.unlink(missing_ok=True)


@router.delete("/{material_id}/vectors", response_model=DeleteVectorsResponse)
def delete_vectors(
    material_id: str,
    user_id: str = Query(..., min_length=1),
) -> DeleteVectorsResponse:
    container = get_container()
    deleted_count = container.qdrant_store.delete_by_material_id(material_id, user_id=user_id)
    return DeleteVectorsResponse(deleted_count=deleted_count)
