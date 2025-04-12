from dbconf import db

from pydantic import BaseModel

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
	images: list[str]
class AttractionResponse(BaseModel):
	nextPage: int | None
	data: list[Attraction]
# /api/attraction/{attractionId}
class AttractionId(BaseModel):
	data: Attraction
# /api/mrts
class Mrts(BaseModel):
	data: list[str]
	

class Attraction:
    def get_with_keyword(page, keyword):
        with db.get_connection() as con:
            with con.cursor(dictionary=True) as cursor:
                offset_num = page*12
                cursor.execute(
                      "SELECT * FROM attraction WHERE mrt=%s or name LIKE %s LIMIT 13 OFFSET %s",
                      (keyword, "%"+keyword+"%", offset_num)
                )
                data = cursor.fetchall()
        return data
    def get_without_keyword(page):
        with db.get_connection() as con:
            with con.cursor(dictionary=True) as cursor:
                offset_num = page*12
                cursor.execute(
                    "SELECT * FROM attraction LIMIT 13 OFFSET %s",
                    (offset_num, )
                )
                data = cursor.fetchall()
        return data
    def get_by_id(attractionId):
        with db.get_connection() as con:
            with con.cursor(dictionary=True) as cursor:
                cursor.execute(
                    "select * from attraction where id = %s",
                    (attractionId, )
                )
                data = cursor.fetchone()
        return data
    def get_mrt():
        with db.get_connection() as con:
            with con.cursor("cursor") as cursor:
                query = """ 
					select mrt, count(id)
					from attraction
					where mrt is not null
					group by mrt
					order by count(id) desc;"""
                cursor.execute(query)
                data = cursor.fetchall()
                result = [x[0] for x in data]
        return result

class Nextpage:
    def count(data, page):
        data_count = len(data)
        if data_count > 12:
            nextpage = page + 1
        else:
            nextpage = None
        return nextpage
     
class Data:
    def process_image(data):
        for spot in data:
            spot["images"] = spot["images"].split(",")
        return data
    def process_response_data_structure(data):
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
        return response_data