from dbconf import db

import os
from dotenv import load_dotenv

import requests

from typing import Literal
from pydantic import BaseModel, EmailStr, HttpUrl
from datetime import date

from model.user import query_userInfo_by_email

load_dotenv()

class Contact(BaseModel):
    name: str
    email: EmailStr
    phone: str
class Attraction(BaseModel):
    id: int
    name: str
    address: str
    image: HttpUrl
class Trip(BaseModel):
    attraction: Attraction
    date: date
    time: Literal['morning', 'afternoon']
class OrderInput(BaseModel):
    class Order(BaseModel):
        booking_id: int
        price: Literal[2000, 2500]
        trip: Trip
        contact: Contact
    prime: str
    order: list[Order]

class OrderGet(BaseModel):
    class Inner(BaseModel):
        number: str
        price: Literal[2000, 2500]
        trip: Trip
        contact: Contact
        status: Literal[0, 1]
    order_cart_id: str
    data: list[Inner] | None

class OrderOutput(BaseModel):
    class OrderResult(BaseModel):
        number: str
        payment: "PaymentStatus"
        class PaymentStatus(BaseModel):
            status: int
            message: str
    data: OrderResult


class Order:
    def create(order, order_cart_id):
        try:
            # 取得member_id
            data = query_userInfo_by_email(order.contact.email)
            member_id = data["id"]
            # 取得order_number
            order_num = Order.create_order_number()

            with db.get_connection() as con:
                with con.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        """
                        insert into orders(order_cart_id, order_number, member_id, attraction_id, go_date, time, price_receivable)
                        values(%s, %s, %s, %s, %s, %s, %s);
                        """,
                        (order_cart_id, order_num, member_id, order.trip.attraction.id, order.trip.date, order.trip.time, order.price)
                    )
                    con.commit()
            return order_num
        except:
            return False
    
    def get_info(order_cart_id, member_id):
        with db.get_connection() as con:
            with con.cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    select order_cart_id, order_number, price_receivable, go_date, time, paid_status, a.id as attraction_id, a.name as attraction_name, a.address, a.images, m.name as member_name, m.email, m.phone 
                    from orders
                    inner join attraction a on orders.attraction_id = a.id
                    inner join member m on orders.member_id = m.id
                    where order_cart_id = %s
                    and member_id = %s;
                    """,
                    (order_cart_id, member_id)
                )
                datas = cursor.fetchall()
        for data in datas:
            image = data["images"].split(",")[0]
            data["images"] = image
        
        return datas

    def create_order_number() -> str:
        with db.get_connection() as con:
            with con.cursor(dictionary=True) as cursor:
                result = cursor.callproc("generate_order_number", [None])
                order_num = result['generate_order_number_arg1']
                con.commit()
        return order_num
    
    def post_prime_to_TapPay(prime, price, contact: Contact) -> dict:
        response = requests.post(
            "https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime",
            json={
                "prime": prime,
                "partner_key": os.getenv("partner_key"),
                "merchant_id": os.getenv("merchant_id"),
                "details":"TapPay Test",
                "amount": price,
                "cardholder": {
                    "phone_number": contact.phone,
                    "name": contact.name,
                    "email": contact.email,
                },
                "remember": True
            },
            headers={
                "x-api-key": os.getenv("partner_key")
            }
        )
        data: dict = response.json()
        return data
    
    def update_paid_status_to_paid(order_num):
        with db.get_connection() as con:
            with con.cursor() as cursor:
                cursor.execute(
                    "update orders set paid_status=%s where order_number=%s",
                    ("PAID", order_num)
                )
                con.commit()
        return True
    
    def save_payment_info(order_number, rec_trade_id):
        with db.get_connection() as con:
            with con.cursor() as cursor:
                cursor.execute(
                    "insert into payment(order_number, rec_trade_id) values(%s, %s)",
                    (order_number, rec_trade_id)
                )
                con.commit()
    
    def save_phone_num(member_id, phone):
        try:
            with db.get_connection() as con:
                with con.cursor() as cursor:
                    cursor.execute(
                        "update member set phone=%s where id=%s",
                        (phone, member_id)
                    )
                    con.commit()
            return True
        except:
            return False
        
class Cart:
    def create_order_cart_number() -> str:
        with db.get_connection() as con:
            with con.cursor(dictionary=True) as cursor:
                result = cursor.callproc("generate_cart_number", [None])
                order_cart_number = result['generate_cart_number_arg1']
                con.commit()
        return order_cart_number
    
    def total_price(cart):
        total_price = 0
        for order in cart:
            total_price += order.price
        return total_price