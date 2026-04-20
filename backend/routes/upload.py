"""Image upload endpoint for nutrition label photos."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from services.image_service import ImageServiceError, save_uploaded_image
from utils.auth import require_jwt
from utils.errors import ApiError


upload_bp = Blueprint("upload", __name__)


@upload_bp.post("/upload-image")
@require_jwt
def upload_image(current_user):
    file_storage = request.files.get("image")
    if file_storage is None:
        raise ApiError("The 'image' file field is required", status_code=400, error_code="missing_image")

    try:
        record = save_uploaded_image(file_storage, user_id=current_user.id)
    except ImageServiceError as exc:
        raise ApiError(str(exc), status_code=400, error_code="image_upload_failed") from exc

    return (
        jsonify(
            {
                "message": "Image uploaded successfully",
                "image_id": record.image_id,
                "image": record.to_dict(),
            }
        ),
        201,
    )
