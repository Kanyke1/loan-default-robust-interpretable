"""
Endpoints to save and serve SHAP artifacts (images / HTML).

Design:
- POST /shap/upload    -> multipart: file (image or html), metadata JSON fields (model, type, sample_id optional)
- GET  /shap/list      -> list available shap artifacts (with URLs)
- GET  /shap/download/{filename} -> serve the file (static file from artifacts/shap/)
"""
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional

router = APIRouter()

SHAP_DIR = os.getenv("SHAP_DIR", "artifacts/shap")
os.makedirs(SHAP_DIR, exist_ok=True)

@router.post("/shap/upload")
async def upload_shap(file: UploadFile = File(...), model: str = Form(...), kind: str = Form(...), sample_id: Optional[str] = Form(None)):
    # sanitize filename and save
    filename = file.filename
    # prefix with model and optional sample id for clarity
    prefix = f"{model}_{sample_id}_" if sample_id else f"{model}_"
    save_name = prefix + filename
    save_path = os.path.join(SHAP_DIR, save_name)
    try:
        with open(save_path, "wb") as fh:
            content = await file.read()
            fh.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse({"message":"uploaded", "path": save_path, "url": f"/shap/download/{save_name}"})

@router.get("/shap/list")
async def list_shap():
    files = []
    for fn in sorted(os.listdir(SHAP_DIR)):
        files.append({"filename": fn, "url": f"/shap/download/{fn}"})
    return JSONResponse({"files": files})

@router.get("/shap/download/{filename}")
async def download_shap(filename: str):
    path = os.path.join(SHAP_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Not found")
    # serve as file response (browser can show images or HTML)
    return FileResponse(path, media_type="application/octet-stream", filename=filename)