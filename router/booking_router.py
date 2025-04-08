from typing import Annotated
from fastapi import *


from dbconf import db
from utils.response import *

from model.user_model import oauth2_scheme, verify_current_user
from model.booking_model import *


booking_router = APIRouter(
    tags=["booking"]
)

connection_pool = db.connectPool()


@booking_router.post(
    "/api/booking", 
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "建立失敗，輸入不正確或其他原因"},
        403: {"model": ErrorResponse, "description": "未登入系統，拒絕存取"},
        500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
    }
)
async def create(
    token: Annotated[str, Depends(oauth2_scheme)],
    attraction: AttractionBody
):  
    try:
        # 驗證current user
        user = verify_current_user(token)
        if user == False:
            return response_error(403, "未登入系統")

        # 確認資料庫有無待訂景點
        check_exist = Booking.check_exist(user, connection_pool)
        if check_exist:
            create = Booking.replace(attraction, user, connection_pool)
        else:
            create = Booking.create_new(attraction, user, connection_pool)
        
        # 確認有無建立成功
        if create == True:
            return {"ok": True}
        else:
            return response_error(400, "建立失敗，輸入不正確或其他原因")
    except:
        return response_error(500, "伺服器內部錯誤")
    

@booking_router.get(
    "/api/booking",
    response_model=BookingData,
    responses={
        403: {"model": ErrorResponse, "description": "未登入系統，拒絕存取"}
    }
)
async def get_booking(token: Annotated[str, Depends(oauth2_scheme)]):
    # 驗證current user
    user = verify_current_user(token)
    if user == False:
        return response_error(403, "未登入系統")

    # 確認有無尚未下單的預定行程資料
    booking = Get.booking(user, connection_pool)
    if booking is None:
        return {"data": None}

    # 取得對應的景點資料
    attraction = Get.attraction(booking, connection_pool)
    images = attraction["images"].split(",")

    # 整理回覆
    result = {
        "data": {
            "attraction": {
                "id": attraction["id"],
                "name": attraction["name"],
                "address": attraction["address"],
                "image": images[0]
            },
            "date": booking["go_date"],
            "time": booking["time"],
            "price": booking["price"]
        }
    }
    return result

@booking_router.delete(
        "/api/booking",
        response_model=SuccessResponse,
        responses={
            403: {"model": ErrorResponse, "description": "未登入系統，拒絕存取"}
        }
)
async def delete(token: Annotated[str, Depends(oauth2_scheme)]):
    user = verify_current_user(token)
    if user == False:
        return response_error(403, "未登入系統")
    
    delete = Booking.delete(user, connection_pool)
    if delete:
        return {"ok": True}


