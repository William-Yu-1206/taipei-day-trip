import os
from dotenv import load_dotenv
from mysql.connector import pooling
load_dotenv()
connection_pool = pooling.MySQLConnectionPool(
	pool_name="day_trip_pool",
	pool_size=5,
	host="localhost",
	user=os.getenv("DB_USER"),
	password=os.getenv("DB_PASSWORD"),
	database=os.getenv("DB_NAME")
)

from typing import Annotated, List, Dict
from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
app=FastAPI()

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
	
# /api/attraction/{attractionId}
class AttractionId(BaseModel):
	data: Attraction

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


# /api/mrts
class Mrts(BaseModel):
	data: List[str]

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
