import os
from dotenv import load_dotenv
import jwt
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone

from dbconf import db


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
	data: User | None

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 7*24*60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/auth")



class member:
	def create(user, hashed_pwd):
		try:
			with db.get_connection() as con:
				with con.cursor(dictionary=True) as cursor:
					cursor.execute(
						"insert into member(name, email, password) values(%s, %s, %s)",
						(user.name, user.email, hashed_pwd)
					)
					con.commit()
			return True
		except:
			return False

# def get_db_connection():
# 	connection = db.get_connection()
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
	
# def query_userInfo_by_id(connection, id):
# 	query = "select id, name, email from member where id = %s"
# 	values = (id, )
# 	return queryOne(connection, query, values)

def query_userInfo_by_email(email):
	with db.get_connection() as con:
		with con.cursor(dictionary=True) as cursor:
			cursor.execute(
				"select id, name, email, password from member where email = %s",
				(email, )
			)
			data = cursor.fetchone()
	return data

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
def verify_current_user(token):
	try:
		user = decode_token(token)
		return user
	except:
		return False