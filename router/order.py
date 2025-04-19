from typing import Annotated
from fastapi import *

from model.order import *
from model.user import oauth2_scheme, verify_current_user
from model.booking import Booking

from utils.response import *

order_router = APIRouter(
    tags=['Order']
)

@order_router.post("/api/orders",
                   response_model=OrderOutput,
                   responses={
                       400: {"model": ErrorResponse, "description": "訂單建立失敗，輸入不正確或其他原因"},
                       403: {"model": ErrorResponse, "description": "未登入系統，拒絕存取"},
                       500: {"model": ErrorResponse, "description": "伺服器內部錯誤"}
                   })
async def create(
    token: Annotated[str, Depends(oauth2_scheme)],
    order: OrderInput
):
    try:
        # 驗證當前用戶
        user = verify_current_user(token)
        if user == False:
            return response_error(403, "未登入系統，拒絕存取")

        # 儲存電話號碼到member資料庫
        Order.save_phone_num(user["sub"], order.order.contact.phone)

        # 建立訂單
        order_num = Order.create(order)
        if order_num == False:
            return response_error(400, "訂單建立失敗，輸入不正確或其他原因")
        
        # 刪除booking資料
        Booking.delete(user["sub"])

        # 發送prime給TapPay
        data = Order.post_prime_to_TapPay(order.prime, order.order.price, order.order.contact)
        status = data.get("status")

        if status == 0:
            Order.update_paid_status_to_paid(order_num)
            Order.save_payment_info(order_num, data.get("rec_trade_id"))
            return {"data": {
                "number": order_num,
                "payment": {
                    "status": status,
                    "message": "付款成功"
                }
            }}
        else:
            return {"data": {
                "number": order_num,
                "payment": {
                    "status": status,
                    "message": data.get("msg")
                }
            }}
    except:
        return response_error(500, "伺服器內部錯誤")

@order_router.get("/api/order/{orderNumber}",
                  response_model=OrderGet,
                  responses={
                       403: {"model": ErrorResponse, "description": "未登入系統，拒絕存取"}
                   })
async def get_order_info(
    token: Annotated[str, Depends(oauth2_scheme)],
    orderNumber: str
):
    # 驗證當前用戶
    user = verify_current_user(token)
    if user == False:
        return response_error(403, "未登入系統，拒絕存取")
    # 取得訂單資料
    data = Order.get_info(orderNumber)
    # 查無此訂單
    if data is None:
        return {"data": None}

    # 整理成功回覆
    images = data["images"].split(",")
    
    status = 0
    if data["paid_status"] == "PAID":
        status = 1

    result = {
        "number": data["order_number"],
        "price": data["price_receivable"],
        "trip": {
            "attraction": {
                "id": data["attraction_id"],
                "name": data["attraction_name"],
                "address": data["address"],
                "image": images[0]
            },
            "date": data["go_date"],
            "time": data["time"]
        },
        "contact": {
            "name": data["member_name"],
            "email": data["email"],
            "phone": data["phone"]
        },
        "status": status
    }
    return {"data": result}
