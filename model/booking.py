from typing import Literal
from pydantic import BaseModel, HttpUrl
from datetime import date
import datetime

from dbconf import db

class AttractionBody(BaseModel):
    attractionId: int
    date: date
    time: str
    price: int

class BookingAttraction(BaseModel):
    id: int
    name: str
    address: str
    image: HttpUrl
class BookingInfo(BaseModel):
    attraction: BookingAttraction
    bookingId: int
    date: date
    time: Literal["morning", "afternoon"]
    price: Literal[2000, 2500]
class BookingData(BaseModel):
    data: list[BookingInfo] | None

class Booking:
    # def check_exist(user):
    #     with db.get_connection() as con:
    #         with con.cursor(dictionary=True) as cursor:
    #             cursor.execute(
    #                 "select member_id, attraction_id from booking where member_id = %s",
    #                 (user["sub"], )
    #             )
    #             data = cursor.fetchone()
    #     if data is None:
    #         return False
    #     else:
    #         return True
    def create_new(attraction, user):
        try:
            with db.get_connection() as con:
                with con.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        "insert into booking(attraction_id, go_date, time, price, member_id) values(%s, %s, %s, %s, %s)",
                        (attraction.attractionId, attraction.date, attraction.time, attraction.price, user["sub"])
                    )
                    con.commit()
            return True
        except:
            return False
    # def replace(attraction, user):
    #     try:
    #         with db.get_connection() as con:
    #             with con.cursor(dictionary=True) as cursor:
    #                 cursor.execute(
    #                     "update booking set attraction_id = %s, go_date = %s, time = %s, price = %s, create_date = %s where member_id = %s",
    #                     (attraction.attractionId, attraction.date, attraction.time, attraction.price, datetime.datetime.now(), user["sub"])
    #                 )
    #                 con.commit()
    #         return True
    #     except:
    #         return False
    def drop(booking_id, member_id):
        try:
            with db.get_connection() as con:
                with con.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        "update booking set cart_status='drop' where id=%s and member_id=%s",
                        (booking_id, member_id)
                    )
                    con.commit()
            return True
        except:
            return False
    def statusToOrder(booking_id, member_id):
        try:
            with db.get_connection() as con:
                with con.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        "update booking set cart_status='order' where id=%s and member_id=%s",
                        (booking_id, member_id)
                    )
                    con.commit()
            return True
        except:
            return False

class Get:
    def booking(member_id):
        with db.get_connection() as con:
            with con.cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    select b.id, b.attraction_id, b.go_date, b.time, b.price, a.name, a.address, a.images
                    from booking b
                    inner join attraction a on b.attraction_id = a.id
                    where b.member_id = %s 
                    and b.cart_status='cart'
                    order by b.id
                    """,
                    (member_id,)
                )
                data = cursor.fetchall()

        for item in data:
            item["images"] = item["images"].split(",")[0]

        return data
    
    # def attraction(attraction_id):
    #     with db.get_connection() as con:
    #         with con.cursor(dictionary=True) as cursor:
    #             placeholders = ", ".join(["%s"] * len(attraction_id))
    #             cursor.execute(
    #                 f"select id, name, address, images from attraction where id in ({placeholders})",
    #                 attraction_id
    #             )
    #             data = cursor.fetchall()

    #     for attraction in data:
    #         attraction["images"] = attraction["images"].split(",")[0]

    #     return data
    
    def response(bookings):
        data = []
        for i in range(len(bookings)):
            booking_info = {
                "attraction": {
                    "id": bookings[i]["attraction_id"],
                    "name": bookings[i]["name"],
                    "address": bookings[i]["address"],
                    "image": bookings[i]["images"]
                },
                "bookingId": bookings[i]["id"],
                "date": bookings[i]["go_date"],
                "time": bookings[i]["time"],
                "price": bookings[i]["price"]
            }
            data.append(booking_info)
        result = {"data": data}
        return result