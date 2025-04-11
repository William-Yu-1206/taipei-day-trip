from typing import Annotated
from fastapi import *

from model.user import *
from utils.response import *

user_router = APIRouter(
	tags=["user"]
)

@user_router.post("/api/user",
		  response_model=SuccessResponse,
		  responses={
			  400: {"model": ErrorResponse, "description": "註冊失敗，重複的 Email 或其他原因"},
			  500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
		  })
async def sign_up(user: UserSignUpInput):
	try:
		# 檢查有沒有重複的email
		data = query_userInfo_by_email(user.email)
		if data:
			return response_error(400, "Email重複")
		
		# 加密
		hashed_pwd = pwd_context.hash(user.password)
		
		# 新增會員
		create = member.create(user, hashed_pwd)
		if create == True:
			return response_ok()
		else:
			return response_error(400, "Email重複")
	
	except Exception as e:
		print(f"錯誤發生:{e}")
		return response_error(500, "伺服器內部錯誤")

@user_router.put("/api/user/auth",
		 response_model=Token,
		 responses={
			 400: {"model": ErrorResponse, "description": "登入失敗，帳號或密碼錯誤或其他原因"},
			 500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
		 })
async def sign_in(user: UserSignInInput):
	try:
		# 取得對應的會員資料，根據request的email
		data = query_userInfo_by_email(user.email)
		if data is None:
			return response_error(400, "此帳號不存在")
		
		# 驗證密碼
		hashed_password = data["password"]
		verified = verify_password(user.password, hashed_password)
		if verified:
			# 產出jwt token
			token = generate_token(data)
			return {"token": token}
		else:
			return response_error(400, "帳號密碼錯誤")
		
	except Exception as e:
		print(f"發生錯誤：{e}")
		return response_error(500, "內部伺服器錯誤")
	
@user_router.get("/api/user/auth", response_model=UserAuth)
async def signed_in(token: Annotated[str | None, Depends(oauth2_scheme)]):
	try:
		# 驗證token
		user = verify_current_user(token)
		if user == False:
			return {"data": None}
		
		# 整理回覆
		data = {
			"id": int(user["sub"]),
			"name": user["name"],
			"email": user["email"]
		}
		return {"data": data}
	
	except Exception as e:
		print(f"發生錯誤：{e}")
		return {"data": None}