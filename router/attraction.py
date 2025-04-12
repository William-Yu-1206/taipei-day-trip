from typing import Annotated
from fastapi import *

from utils.response import *
from dbconf import db

from model.attraction import *

attraction_router = APIRouter(
    tags=["Attraction"]
)


@attraction_router.get("/api/attractions",
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
		if keyword:
			data = Attraction.get_with_keyword(page, keyword)
		else:
			data = Attraction.get_without_keyword(page)
		# identify nextpage
		nextpage = Nextpage.count(data, page)
		
        # process data structure of images
		data = data[0:12]
		data = Data.process_image(data)
		
		# process data structure of response
		response_data = Data.process_response_data_structure(data)

		response = {
			"nextPage": nextpage,
			"data": response_data
		}
		return response
	except Exception as e:
		print({e})
		return JSONResponse(content={"error": True, "message": "請按照情境提供對應的錯誤訊息"}, status_code=500)
	
@attraction_router.get("/api/attraction/{attractionId}",
	response_model=AttractionId,
	responses={
		400: {"description": "景點編號不正確", "model": ErrorResponse},
		500: {"description": "伺服器內部錯誤", "model": ErrorResponse}			 
	}
)
async def attractionId(attractionId: Annotated[int, Path(description="景點編號")]):
    try:
        data = Attraction.get_by_id(attractionId)
        if data is None:
            return JSONResponse(content={"error": True, "message": "景點編號不正確"}, status_code=400) 

        # process images
        data["images"] = data["images"].split(",")
        
        # process response
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

@attraction_router.get("/api/mrts",
		 response_model=Mrts,
		 responses={
			 500: {"description": "伺服器內部錯誤", "model": ErrorResponse}
		 })
async def api_mrt():
    try:
        data = Attraction.get_mrt()
        return {"data": data}
    except Exception as e:
        print({e})
        return JSONResponse(content={"error": True, "message": "伺服器錯誤"}, status_code=500)