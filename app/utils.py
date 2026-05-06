from fastapi.responses import JSONResponse

def openai_error(status_code: int, message: str, error_type: str = "api_error"):
    return JSONResponse(
        status_code=status_code,
        content={"error": {"message": message, "type": error_type, "code": status_code}}
    )
