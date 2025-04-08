# import os
# from dotenv import load_dotenv
# import jwt
# from typing import Annotated
from fastapi import *
# from fastapi.responses import JSONResponse
# from fastapi.security import OAuth2PasswordBearer
# from passlib.context import CryptContext
# from pydantic import BaseModel, EmailStr
# from datetime import datetime, timedelta, timezone

from model.user_model import *

user_router = APIRouter(
	tags=["user"]
)

# from dbconf import db
# connection_pool = db.connectPool()

# user_router = APIRouter(
#     tags=["user"]
# )

# class SuccessResponse(BaseModel):
# 	ok: bool
# class ErrorResponse(BaseModel):
# 	error: bool
# 	message: str
# class UserSignUpInput(BaseModel):
# 	name: str
# 	email: EmailStr
# 	password: str
# class UserSignInInput(BaseModel):
# 	email: EmailStr
# 	password: str
# class UserPayload(BaseModel):
# 	sub: str
# 	name: str
# 	email: str
# 	exp: datetime
# 	iat: datetime
# class Token(BaseModel):
# 	token: str
# class User(BaseModel):
# 	id: int	
# 	name: str 
# 	email: EmailStr
# class UserAuth(BaseModel):
# 	data: User | None

# load_dotenv()
# SECRET_KEY = os.getenv("SECRET_KEY")
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 7*24*60

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/user/auth")




# def response_error(status_code, message):
# 	content = {
# 		"error": True,
# 		"message": message
# 	}
# 	return JSONResponse(content=content, status_code=status_code)

# def response_ok():
# 	return {"ok": True}

# def get_db_connection():
# 	connection = connection_pool.get_connection()
# 	try:
# 		yield connection
# 	finally:
# 		connection.close()

# def queryOne(connection, query:str, value:tuple | None = None):
# 	with connection.cursor(dictionary=True) as cursor:
# 		if value is not None:
# 			cursor.execute(query, value)
# 		else:
# 			cursor.execute(query)
# 		data = cursor.fetchone()
# 		return data
# def query_userInfo_by_email(connection, email):
# 	query = "select id, name, email, password from member where email = %s"
# 	values = (email, )
# 	return queryOne(connection, query, values)
# def query_userInfo_by_id(connection, id):
# 	query = "select id, name, email from member where id = %s"
# 	values = (id, )
# 	return queryOne(connection, query, values)

# def verify_password(password, hash) -> bool:
# 	return pwd_context.verify(password, hash)

# def generate_token(data: dict ,key=SECRET_KEY, algorithm=ALGORITHM):
# 	user_payload = {
# 		"sub": str(data["id"]),
# 		"name": data["name"],
# 		"email": data["email"],
# 		"exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
# 		"iat": datetime.now(timezone.utc)
# 	}
# 	return jwt.encode(user_payload, key, algorithm)
# def decode_token(token):
# 	result = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
# 	return result






@user_router.post("/api/user",
		  response_model=SuccessResponse,
		  responses={
			  400: {"model": ErrorResponse, "description": "註冊失敗，重複的 Email 或其他原因"},
			  500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
		  })
async def sign_up(user: UserSignUpInput, connection=Depends(get_db_connection)):
	try:
		# 取得資料庫資料，根據request的email
		data = query_userInfo_by_email(connection, user.email)
			
		if data:
			return response_error(400, "Email重複")
		
		# 加密
		hashed_pwd = pwd_context.hash(user.password)
		
		# 新增會員
		with connection.cursor() as cursor:
			query = "insert into member(name, email, password) values(%s, %s, %s)"
			values = (user.name, user.email, hashed_pwd)
			cursor.execute(query, values)
			connection.commit()
			
		return response_ok()
	
	except Exception as e:
		print(e)
		return response_error(500, "伺服器內部錯誤")

@user_router.put("/api/user/auth",
		 response_model=Token,
		 responses={
			 400: {"model": ErrorResponse, "description": "登入失敗，帳號或密碼錯誤或其他原因"},
			 500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
		 })
async def sign_in(user: UserSignInInput, connection=Depends(get_db_connection)):
	try:
		# 取得資料庫資料，根據request的email
		data = query_userInfo_by_email(connection, user.email)
		if data is None:
			return response_error(400, "此帳號不存在")
		
		# 驗證密碼
		hashed_password = data["password"]
		verified = verify_password(user.password, hashed_password)
		if verified:
			# 產出jwt token
			token = generate_token(data, SECRET_KEY, ALGORITHM)
			return {"token": token}
		
		else:
			return response_error(400, "帳號密碼錯誤")
		
	except Exception as e:
		print(e)
		return response_error(500, "內部伺服器錯誤")
	
@user_router.get("/api/user/auth", response_model=UserAuth)
async def signed_in(token: Annotated[str | None, Depends(oauth2_scheme)]):
	try:
		user = decode_token(token)
		data = {
			"id": int(user["sub"]),
			"name": user["name"],
			"email": user["email"]
		}
		return {"data": data}
	except jwt.PyJWKError as e:
		print(e)
		return {"data": None}
	except Exception as e:
		print(e)
		return {"data": None}