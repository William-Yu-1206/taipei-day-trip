from fastapi.responses import JSONResponse
from pydantic import BaseModel

class SuccessResponse(BaseModel):
	ok: bool
class ErrorResponse(BaseModel):
	error: bool
	message: str
	
def response_error(status_code, message):
	content = {
		"error": True,
		"message": message
	}
	return JSONResponse(content=content, status_code=status_code)

def response_ok() -> SuccessResponse:
	return {"ok": True}