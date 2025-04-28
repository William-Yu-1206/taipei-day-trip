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
    data: OrderInput
):
    try:
        # 驗證當前用戶
        user = verify_current_user(token)
        if user == False:
            return response_error(403, "未登入系統，拒絕存取")

        prime = data.prime
        carts = data.order

        #儲存電話號碼到member資料庫
        Order.save_phone_num(user["sub"], carts[0].contact.phone)
        
        # 建立購物車編號
        order_cart_id = Cart.create_order_cart_number()
        # 建立訂單
        order_nums = []
        for order in carts:
            num = Order.create(order, order_cart_id)
            if num == False:
                return response_error(400, "訂單建立失敗，輸入不正確或其他原因")
            order_nums.append(num)

        # # 更改booking狀態 transform cart to order
        for order in carts:
            Booking.statusToOrder(order.booking_id, user["sub"])

        # 計算total price
        total_price = Cart.total_price(carts)

        # 發送prime給TapPay
        data = Order.post_prime_to_TapPay(prime, total_price, order.contact)
        status = data.get("status")

        if status == 0:
            for order_num in order_nums:
                Order.update_paid_status_to_paid(order_num)
                Order.save_payment_info(order_num, data.get("rec_trade_id"))
            return {"data": {
                "number": order_cart_id,
                "payment": {
                    "status": status,
                    "message": "付款成功"
                }
            }}
        else:
            return {"data": {
                "number": order_cart_id,
                "payment": {
                    "status": status,
                    "message": data.get("msg")
                }
            }}
    except:
        return response_error(500, "伺服器內部錯誤")
    

@order_router.get("/api/order/{order_cart_id}",
                #   response_model=OrderGet,
                  responses={
                       403: {"model": ErrorResponse, "description": "未登入系統，拒絕存取"}
                   })
async def get_order_info(
    token: Annotated[str, Depends(oauth2_scheme)],
    order_cart_id: str
):
    # 驗證當前用戶
    user = verify_current_user(token)
    if user == False:
        return response_error(403, "未登入系統，拒絕存取")
    # 取得訂單資料
    orders = Order.get_info(order_cart_id, user["sub"])

    # 查無此訂單
    if orders is None:
        return {"data": None}

    # 整理成功回覆   
    result = []
    for order in orders:
        status = 0
        if order["paid_status"] == "PAID":
            status = 1
        data = {
            "number": order["order_number"],
            "price": order["price_receivable"],
            "trip": {
                "attraction": {
                    "id": order["attraction_id"],
                    "name": order["attraction_name"],
                    "address": order["address"],
                    "image": order["images"]
                },
                "date": order["go_date"],
                "time": order["time"]
            },
            "contact": {
                "name": order["member_name"],
                "email": order["email"],
                "phone": order["phone"]
            },
            "status": status
        }
        result.append(data)
    return {
        "order_cart_id": orders[0]["order_cart_id"],
        "data": result
    }
