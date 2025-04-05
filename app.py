import os
from dotenv import load_dotenv
from mysql.connector import pooling, Error as MySQLError
load_dotenv()
connection_pool = pooling.MySQLConnectionPool(
	pool_name="day_trip_pool",
	pool_size=5,
	host="localhost",
	user=os.getenv("DB_USER"),
	password=os.getenv("DB_PASSWORD"),
	database=os.getenv("DB_NAME")
)

from datetime import datetime, timedelta, timezone

import jwt
from typing import Annotated, List
from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

app=FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Static Pages (Never Modify Code in this Block)
@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/index.html", media_type="text/html")
@app.get("/attraction/{id}", include_in_schema=False)
async def attraction(request: Request, id: int):
	return FileResponse("./static/attraction.html", media_type="text/html")
@app.get("/booking", include_in_schema=False)
async def booking(request: Request):
	return FileResponse("./static/booking.html", media_type="text/html")
@app.get("/thankyou", include_in_schema=False)
async def thankyou(request: Request):
	return FileResponse("./static/thankyou.html", media_type="text/html")


class SuccessResponse(BaseModel):
	ok: bool
class ErrorResponse(BaseModel):
	error: bool
	message: str
# /api/attractions
class Attraction(BaseModel):
	id: int
	name: str
	category: str
	description: str
	address: str
	transport: str
	mrt: str | None
	lat: float
	lng: float
	images: List[str]
class AttractionResponse(BaseModel):
	nextPage: int | None
	data: List[Attraction]
# /api/attraction/{attractionId}
class AttractionId(BaseModel):
	data: Attraction
# /api/mrts
class Mrts(BaseModel):
	data: List[str]
class UserSignUpInput(BaseModel):
	name: str
	email: EmailStr
	password: str
class UserSignInInput(BaseModel):
	email: EmailStr
	password: str
class UserPayload(BaseModel):
	sub: str
	name: str
	email: str
	exp: datetime
	iat: datetime
class Token(BaseModel):
	token: str
class User(BaseModel):
	id: int	
	name: str 
	email: EmailStr
class UserAuth(BaseModel):
	data: User

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 7*24*60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/user/auth")


def response_error(status_code, message):
	content = {
		"error": True,
		"message": message
	}
	return JSONResponse(content=content, status_code=status_code)

def response_ok():
	return {"ok": True}

def get_db_connection():
	connection = connection_pool.get_connection()
	try:
		yield connection
	finally:
		connection.close()

def queryOne(connection, query:str, value:tuple | None = None):
	with connection.cursor(dictionary=True) as cursor:
		if value is not None:
			cursor.execute(query, value)
		else:
			cursor.execute(query)
		data = cursor.fetchone()
		return data
def query_userInfo_by_email(connection, email):
	query = "select id, name, email, password from member where email = %s"
	values = (email, )
	return queryOne(connection, query, values)
def query_userInfo_by_id(connection, id):
	query = "select id, name, email from member where id = %s"
	values = (id, )
	return queryOne(connection, query, values)

def verify_password(password, hash) -> bool:
	return pwd_context.verify(password, hash)

def generate_token(data: dict ,key=SECRET_KEY, algorithm=ALGORITHM):
	user_payload = {
		"sub": str(data["id"]),
		"name": data["name"],
		"email": data["email"],
		"exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
		"iat": datetime.now(timezone.utc)
	}
	return jwt.encode(user_payload, key, algorithm)
def decode_token(token):
	result = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
	return result

@app.get("/api/attractions",
	response_model=AttractionResponse,
	responses={
		500: {"description": "伺服器內部錯誤", "model": ErrorResponse}
	}
)
async def attractions(
	page: Annotated[int, Query(ge=0, description="要取得的分頁，每頁 12 筆資料")],
	keyword: Annotated[str, Query(description="用來完全比對捷運站名稱、或模糊比對景點名稱的關鍵字，沒有給定則不做篩選")] = None
):
	try:
		page = page
		# connect to connection_pool_day_trip
		with connection_pool.get_connection() as connection:
			with connection.cursor(dictionary=True) as cursor:
				# query data depend on keyword
				if keyword:
					query = "SELECT * FROM attraction WHERE mrt=%s or name LIKE %s LIMIT 13 OFFSET %s"
					offset_num = page*12
					values = (keyword, "%"+keyword+"%", offset_num)
					cursor.execute(query, values)
					data = cursor.fetchall()
				else:
					query = "SELECT * FROM attraction LIMIT 13 OFFSET %s"
					offset_num = page*12
					values = (offset_num, )
					cursor.execute(query, values)
					data = cursor.fetchall()
		# identify nextpage
		data_count = len(data)
		if data_count > 12:
			nextpage = page + 1
		else:
			nextpage = None

		data = data[0:12]
					
		# process data structure of images
		for spot in data:
			spot["images"] = spot["images"].split(",")
		
		# process data structure of response
		response_data = []
		for spot in data:
			response_data.append(
				{
					"id": spot["id"],
					"name": spot["name"],
					"category": spot["category"],
					"description": spot["description"], 
					"address": spot["address"],
					"transport": spot["transport"],
					"mrt": spot["mrt"],
					"lat": spot["lat"],
					"lng": spot["lng"],
					"images": spot["images"] 
				}
			)

		response = {
			"nextPage": nextpage,
			"data": response_data
		}
		return response
	except Exception as e:
		print({e})
		return JSONResponse(content={"error": True, "message": "請按照情境提供對應的錯誤訊息"}, status_code=500)
	
@app.get("/api/attraction/{attractionId}",
	response_model=AttractionId,
	responses={
		400: {"description": "景點編號不正確", "model": ErrorResponse},
		500: {"description": "伺服器內部錯誤", "model": ErrorResponse}			 
	}
)
async def attractionId(attractionId: Annotated[int, Path(description="景點編號")]):
	try:
		with connection_pool.get_connection() as connection:
			with connection.cursor(dictionary=True) as cursor:
				query = "select * from attraction where id = %s"
				values = (attractionId, )
				cursor.execute(query, values)
				data = cursor.fetchone()
				if data is None:
					return JSONResponse(content={"error": True, "message": "景點編號不正確"}, status_code=400) 
				else:
					data["images"] = data["images"].split(",")
					response_data = {
						"id": data["id"],
						"name": data["name"],
						"category": data["category"],
						"description": data["description"], 
						"address": data["address"],
						"transport": data["transport"],
						"mrt": data["mrt"],
						"lat": data["lat"],
						"lng": data["lng"],
						"images": data["images"],
					}
					return {"data": response_data}
	except Exception as e:
		print({e})
		return JSONResponse(content={"error": True, "message": "伺服器錯誤"}, status_code=500) 

@app.get("/api/mrts",
		 response_model=Mrts,
		 responses={
			 500: {"description": "伺服器內部錯誤", "model": ErrorResponse}
		 })
async def api_mrt():
	try:
		with connection_pool.get_connection() as connection:
			with connection.cursor("cursor") as cursor:
				query = """ 
					select mrt, count(id)
					from attraction
					where mrt is not null
					group by mrt
					order by count(id) desc;"""
				cursor.execute(query)
				data = cursor.fetchall()
				result = [x[0] for x in data]
				return {"data": result}
	except Exception as e:
		print({e})
		return JSONResponse(content={"error": True, "message": "伺服器錯誤"}, status_code=500)

@app.post("/api/user",
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
	
	except MySQLError as e:
		print(e)
		return response_error(500, "資料庫連線錯誤")
	except Exception as e:
		print(e)
		return response_error(500, "伺服器內部錯誤")

@app.put("/api/user/auth",
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
	
@app.get("/api/user/auth", response_model=UserAuth | None)
async def signed_in(token: Annotated[str | None, Depends(oauth2_scheme)]):
	try:
		user = decode_token(token)
		data = {
			"id": int(user["sub"]),
			"name": user["name"],
			"email": user["email"]
		}
		print(data)
		return {"data": data}
	except jwt.PyJWKError as e:
		print(e)
		return None
	except Exception as e:
		print(e)
		return None

