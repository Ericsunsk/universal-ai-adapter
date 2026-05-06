import base64
import json
import time
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import load_config, save_config, ADMIN_PASSWORD, logger
from app.utils import openai_error
from app.adapter import AdapterCore

router = APIRouter()
security = HTTPBearer()

def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    return credentials.credentials

@router.get("/")
async def admin_page():
    return FileResponse("static/index.html")

@router.get("/api/config")
async def get_cfg(x_admin_password: Optional[str] = Header(None)):
    if x_admin_password != ADMIN_PASSWORD: raise HTTPException(status_code=403)
    return load_config()

@router.post("/api/config")
async def update_cfg(data: dict, x_admin_password: Optional[str] = Header(None)):
    if x_admin_password != ADMIN_PASSWORD: raise HTTPException(status_code=403)
    save_config(data.get("config"))
    return {"status": "success"}

async def execute_adapter_task(api_key: str, model: str, prompt: str, size: str, urls: list, extra_params: dict, request: Request, endpoint_name: str):
    if not prompt:
        return openai_error(400, "Prompt is required", "invalid_request_error")
        
    config = load_config()
    adapter = AdapterCore(api_key, model, config, request.app.state.http_client)
    try:
        url = await adapter.handle_async_polling(prompt, size, urls, extra_params)
        if not url: 
            return openai_error(504, "Upstream provider timeout", "timeout")
        return {"created": int(time.time()), "data": [{"url": url}]}
    except ValueError as e:
        return openai_error(400, str(e), "invalid_request_error")
    except Exception as e:
        logger.error(f"{endpoint_name} error: {e}")
        return openai_error(500, str(e))

@router.get("/v1/models")
async def list_models(request: Request, api_key: str = Depends(get_api_key)):
    config = load_config()
    models = set()
    for d_id, d_cfg in config.get("drivers", {}).items():
        for m in d_cfg.get("models", []):
            models.add(m)
            
    data = []
    for m in sorted(models):
        data.append({
            "id": m,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "universal-adapter"
        })
        
    return {
        "object": "list",
        "data": data
    }

@router.post("/v1/images/generations")
async def generations(request: Request, api_key: str = Depends(get_api_key)):
    try:
        body = await request.json()
    except Exception:
        return openai_error(400, "Invalid JSON body", "invalid_request_error")
        
    model = body.get("model", "default").lower()
    prompt = body.get("prompt")
    size = body.get("size", "1024x1024")
    
    urls = body.get("image_urls")
    if not urls and body.get("image"):
        urls = [body.get("image")]

    extra_params = {k: v for k, v in body.items() if k not in ["model", "prompt", "size", "image_urls", "image"]}

    return await execute_adapter_task(api_key, model, prompt, size, urls, extra_params, request, "Generation")

@router.post("/v1/images/edits")
async def edits(request: Request, api_key: str = Depends(get_api_key)):
    try:
        form = await request.form()
    except Exception as e:
        return openai_error(400, f"Invalid form data: {e}", "invalid_request_error")

    model = form.get("model", "default").lower()
    prompt = form.get("prompt", "")
    size = form.get("size", "1024x1024")
    
    urls = []
    for image_file in form.getlist("image"):
        if hasattr(image_file, "read"):
            img_bytes = await image_file.read()
            mime_type = getattr(image_file, "content_type", "image/png")
            urls.append(f"data:{mime_type};base64," + base64.b64encode(img_bytes).decode('utf-8'))
            
    for mask_file in form.getlist("mask"):
        if hasattr(mask_file, "read"):
            mask_bytes = await mask_file.read()
            mime_type = getattr(mask_file, "content_type", "image/png")
            urls.append(f"data:{mime_type};base64," + base64.b64encode(mask_bytes).decode('utf-8'))
            
    extra_params = {}
    for k, v in form.items():
        if k not in ["model", "prompt", "size", "image", "mask"]:
            if isinstance(v, str):
                try:
                    v = json.loads(v)
                except ValueError:
                    pass
            extra_params[k] = v

    return await execute_adapter_task(api_key, model, prompt, size, urls, extra_params, request, "Edits")
