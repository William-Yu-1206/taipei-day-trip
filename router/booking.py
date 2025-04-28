from typing import Annotated
from fastapi import *

from utils.response import SuccessResponse, ErrorResponse, response_error

from model.user import oauth2_scheme, verify_current_user
from model.booking import *


booking_router = APIRouter(
    tags=["booking"]
)

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
        # 建立訂單
        create = Booking.create_new(attraction, user)
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
    bookings = Get.booking(user["sub"])
    if bookings == []:
        return {"data": None}

    # 回覆
    result = Get.response(bookings)
    return result


@booking_router.patch(
        "/api/booking/{booking_id}",
        response_model=SuccessResponse,
        responses={
            403: {"model": ErrorResponse, "description": "未登入系統，拒絕存取"}
        }
)
async def drop_cart(
    token: Annotated[str, Depends(oauth2_scheme)],
    booking_id: int
):
    user = verify_current_user(token)
    if user == False:
        return response_error(403, "未登入系統")

    drop = Booking.drop(booking_id, int(user["sub"]))
    if drop:
        return {"ok": True}


